"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
import logging
import json

from courseware.models import StudentModule

from student.models import CourseEnrollment, anonymous_id_for_user

from submissions import api as submissions_api
from submissions.models import StudentItem as SubmissionsStudent

from django.core.exceptions import PermissionDenied
from django.template import Context, Template

from webob.response import Response

from xblock.core import XBlock
from xblock.fields import Scope, Float, String, Boolean
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


def reify(meth):
    """
    Decorator which caches value so it is only computed once.
    Keyword arguments:
    inst
    """
    def getter(inst):
        """
        Set value to meth name in dict and returns value.
        """
        value = meth(inst)
        inst.__dict__[meth.__name__] = value
        return value
    return property(getter)


class FlexibleGradingXBlock(XBlock):

    """
    This block defines a grading unit which can then be graded 
    by staff.
    """

    has_score = True
    icon_class = 'problem'

    display_name = String(
        display_name="Display name",
        default="Flex Grader",
        help="This name appears in the horizontal navigation at the top of "
             "the page.",
        scope=Scope.settings,
    )

    weight = Float(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": .1},
        scope=Scope.settings
    )

    points = Float(
        display_name="Maximum score",
        help=("Maximum grade score given to assignment by staff."),
        values={"min": 0, "step": .1},
        default=100,
        scope=Scope.settings
    )

    score = Float(
        display_name="Grade score",
        default=None,
        help=("Grade score given to assignment by staff."),
        values={"min": 0, "step": .1},
        scope=Scope.user_state
    )

    comment = String(
        display_name="Instructor comment",
        default='',
        scope=Scope.user_state,
        help="Feedback given to student by instructor."
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def max_score(self):
        return self.points

    @reify
    def block_id(self):
        """
        Return the usage_id of the block.
        """
        return self.scope_ids.usage_id

    def student_view(self, context=None):
        """
        The primary view of the FlexibleGradingXBlock, shown to students
        when viewing courses.
        """

        context = {
            "student_state": json.dumps(self.student_state()),
            "id": self.location.name.replace('.', '_')
        }

        if self.show_staff_grading_interface():
            context['is_course_staff'] = True

        fragment = Fragment()
        fragment.add_content(
            render_template(
                'templates/flexible_grader/show.html',
                context
            )
        )

        fragment.add_css(
            self.resource_string("static/css/flexible_grader.css"))
        fragment.add_javascript(
            self.resource_string("static/js/src/flexible_grader.js"))
        fragment.initialize_js('FlexibleGradingXBlock')

        return fragment

    def student_state(self):
        """
        Returns a JSON serializable representation of student's state for
        rendering in client view.
        """

        score = self.score
        if score is not None:
            graded = {'score': score, 'comment': self.comment}
        else:
            graded = None

        return {
            "display_name": self.display_name,
            "graded": graded,
            "max_score": self.max_score()
        }

    def studio_view(self, context=None):
        try:
            cls = type(self)

            def none_to_empty(x):
                return x if x is not None else ''

            edit_fields = (
                (field, none_to_empty(getattr(self, field.name)), validator)
                for field, validator in (
                    (cls.display_name, 'string'),
                    (cls.points, 'number'),
                    (cls.weight, 'number')
                )
            )

            context = {
                'fields': edit_fields
            }

            fragment = Fragment()
            fragment.add_content(
                render_template(
                    'templates/flexible_grader/edit.html',
                    context
                )
            )

            fragment.add_javascript(
                self.resource_string("static/js/src/studio.js"))
            fragment.initialize_js('FlexibleGradingXBlock')

            return fragment
        except:
            log.error("Don't swallow my exceptions", exc_info=True)
            raise

    def student_submission_id(self, anonymous_student_id=None):
        # pylint: disable=no-member
        """
        Returns dict required by the submissions app for creating and
        retrieving submissions for a particular student.
        """
        if anonymous_student_id is None:
            anonymous_student_id = self.xmodule_runtime.anonymous_student_id
        return {
            "student_id": anonymous_student_id,
            "course_id": self.course_id,
            "item_id": self.block_id,
            "item_type": 'sga',  # ???
        }

    def get_submission(self, submission_id=None):
        """
        Get student's most recent submission.
        """
        submissions = submissions_api.get_submissions(
            self.student_submission_id(submission_id))
        if submissions:
            # If I understand docs correctly, most recent submission should
            # be first
            return submissions[0]

    def get_score(self, anonymous_student_id=None):
        """
        Return student's current score.
        """
        student_item = self.student_submission_id(anonymous_student_id)
        score = submissions_api.get_score(student_item)
        if score:
            return score['points_earned']

    def staff_grading_data(self):
        def get_student_data(user):
            module, created = StudentModule.objects.get_or_create(
                course_id=self.course_id,
                module_state_key=self.location,
                student=user,
                defaults={
                    'state': '{}',
                    'module_type': self.category,
                })

            if created:
                log.info(
                    "Init for course:%s module:%s student:%s  ",
                    module.course_id,
                    module.module_state_key,
                    module.student.username
                )

            state = json.loads(module.state)
            anonymous_student_id = anonymous_id_for_user(user, self.course_id)
            score = self.get_score(anonymous_student_id)

            return {
                'module_id': module.id,
                'username': module.student.username,
                'email': module.student.email,
                'comment': state.get("comment", '')
            }

        enrolled_students = (
            CourseEnrollment
            .users_enrolled_in(self.xmodule_runtime.course_id)
        )

        return {
            'assignments': [get_student_data(student) for student
                            in enrolled_students],
            'max_score': self.max_score()
        }

    @XBlock.handler
    def get_staff_grading_data(self, request, suffix=''):
        # pylint: disable=unused-argument
        """
        Return the html for the staff grading view
        """
        require(self.is_course_staff())
        return Response(json_body=self.staff_grading_data())

    @XBlock.json_handler
    def save_flexible_grader(self, data, suffix=''):
        for name in ('display_name', 'points', 'weight'):
            setattr(self, name, data.get(name, getattr(self, name)))

    def is_course_staff(self):
        # pylint: disable=no-member
        """
         Check if user is course staff.
        """
        return getattr(self.xmodule_runtime, 'user_is_staff', False)

    def show_staff_grading_interface(self):
        in_studio_preview = self.scope_ids.user_id is None
        return self.is_course_staff() and not in_studio_preview


def load_resource(resource_path):
    """
    Gets the content of a resource
    """
    resource_content = pkg_resources.resource_string(__name__, resource_path)
    return unicode(resource_content)


def render_template(template_path, context={}):
    """
    Evaluate a template by resource path, applying the provided context
    """
    template_str = load_resource(template_path)
    template = Template(template_str)
    return template.render(Context(context))


def require(assertion):
    """
    Raises PermissionDenied if assertion is not true.
    """
    if not assertion:
        raise PermissionDenied
