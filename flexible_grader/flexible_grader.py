"""TO-DO: Write a description of what this XBlock is."""

import datetime
import pkg_resources
import logging
import json
import pytz

from courseware.models import StudentModule

from student.models import CourseEnrollment, anonymous_id_for_user

from submissions import api as submissions_api
from submissions.models import StudentItem as SubmissionsStudent

from django.core.exceptions import PermissionDenied
from django.template import Context, Template

from webob.response import Response

from xblock.core import XBlock
from xblock.fields import Scope, Float, String, Boolean, Integer
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

    points = Integer(
        display_name="Maximum score",
        help=("Maximum grade score given to assignment by staff."),
        default=100,
        scope=Scope.settings
    )

    comment = String(
        display_name="Instructor comment",
        default='',
        scope=Scope.user_state,
        help="Feedback given to student by instructor."
    )

    def max_score(self):
        """
        Return the maximum score possible.
        """
        return self.points

    @reify
    def block_id(self):
        """
        Return the usage_id of the block.
        """
        return self.scope_ids.usage_id

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

    @reify
    def score(self):
        """
        Return score from submissions.
        """
        return self.get_score()

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
            self.update_staff_debug_context(context)

        fragment = Fragment()
        fragment.add_content(
            render_template(
                'templates/flexible_grader/show.html',
                context
            )
        )

        data = {
            "image_url": self.runtime.local_resource_url(
                self, 'public/images/spinner.gif'
            )
        }

        loader_css = """
        .sga-spinner-icon {{ 
            background: url('{image_url}') no-repeat left center;
            padding-right: 20px;
         }}
        """.format(**data)

        fragment.add_css(loader_css)
        fragment.add_css(_resource("static/css/flexible_grader.css"))
        fragment.add_javascript(_resource("static/js/src/flexible_grader.js"))
        fragment.add_javascript(_resource("static/js/src/jquery.blockUI.js"))
        fragment.initialize_js('FlexibleGradingXBlock')

        return fragment

    def update_staff_debug_context(self, context):
        # pylint: disable=no-member
        """
        Add context info for the Staff Debug interface.
        """
        published = self.start
        context['is_released'] = published and published < _now()
        context['location'] = self.location
        context['category'] = type(self).__name__
        context['fields'] = [
            (name, field.read_from(self))
            for name, field in self.fields.items()]

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

    def staff_grading_data(self):
        """
        Return student assignment information for display on the
        grading screen.
        """
        def get_student_data(user):
            # pylint: disable=no-member
            """
            Returns a dict of student assignment information along with
            student id and module id, this information will be used 
            on grading screen
            """
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
            student_score = self.get_score(anonymous_student_id)
            submission_id = ''
            submission = self.get_submission(anonymous_student_id)
            if submission:
                submission_id = submission['uuid']

            return {
                'module_id': module.id,
                'student_id': anonymous_student_id,
                'submission_id': submission_id,
                'username': module.student.username,
                'fullname': module.student.profile.name,
                'email': module.student.email,
                'score': student_score,
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

            fragment.add_javascript(_resource("static/js/src/studio.js"))
            fragment.initialize_js('FlexibleGradingXBlock')

            return fragment
        except:
            log.error("Don't swallow my exceptions", exc_info=True)
            raise

    @XBlock.handler
    def get_staff_grading_data(self, request, suffix=''):
        # pylint: disable=unused-argument
        """
        Return the html for the staff grading view
        """
        require(self.is_course_staff())
        return Response(json_body=self.staff_grading_data())

    def submit_grade(self, module_id, submission_id, score, comment):
        module = StudentModule.objects.get(pk=module_id)
        state = json.loads(module.state)

        if submission_id:
            uuid = submission_id
        else:
            anonymous_student_id = (
                anonymous_id_for_user(module.student, self.course_id)
            )

            answer = ""
            student_item = self.student_submission_id(anonymous_student_id)
            submissions_api.create_submission(student_item, answer)
            submission = self.get_submission(anonymous_student_id)
            uuid = submission['uuid']

        submissions_api.set_score(uuid, score, self.max_score())
        state['comment'] = comment
        module.state = json.dumps(state)
        module.save()
        log.info(
            "enter_grade for course:%s module:%s student:%s",
            module.course_id,
            module.module_state_key,
            module.student.username
        )

    @XBlock.handler
    def enter_grade(self, request, suffix=''):
        # pylint: disable=unused-argument
        """
        Persist scores for multiple students given by staff.
        """
        require(self.is_course_staff())
        students = json.loads(request.params['students'])
        for student in students:
            self.submit_grade(module_id=student['module_id'],
                              submission_id=student['submission_id'],
                              score=int(student['grade']),
                              comment=student.get('comment', ''))

        return Response(json_body=self.staff_grading_data())

    def reset_score(self, student_id, module_id):
        # pylint: disable=unused-argument
        """
        Reset a student's score.
        """
        submissions_api.reset_score(student_id, self.course_id, self.block_id)
        module = StudentModule.objects.get(pk=module_id)
        state = json.loads(module.state)
        state['comment'] = ''
        module.state = json.dumps(state)
        module.save()
        log.info(
            "remove_grade for course:%s module:%s student:%s",
            module.course_id,
            module.module_state_key,
            module.student.username
        )

    @XBlock.handler
    def remove_grade(self, request, suffix=''):
        # pylint: disable=unused-argument
        """
        Reset a students score request by staff.
        """
        require(self.is_course_staff())
        student_id = request.params['student_id']
        module_id = request.params['module_id']
        self.reset_score(student_id, module_id)

        return Response(json_body=self.staff_grading_data())

    @XBlock.json_handler
    def save_flexible_grader(self, data, suffix=''):
        # pylint: disable=unused-argument
        """
        Persist block data when updating settings in studio.
        """
        self.display_name = data.get('display_name', self.display_name)

        # Validate points before saving
        points = data.get('points', self.points)
        # Check that we are an int
        try:
            points = int(points)
        except ValueError:
            raise JsonHandlerError(400, 'Points must be an integer')
        # Check that we are positive
        if points < 0:
            raise JsonHandlerError(400, 'Points must be a positive integer')
        self.points = points

        # Validate weight before saving
        weight = data.get('weight', self.weight)
        # Check that weight is a float.
        if weight:
            try:
                weight = float(weight)
            except ValueError:
                raise JsonHandlerError(400, 'Weight must be a decimal number')
            # Check that we are positive
            if weight < 0:
                raise JsonHandlerError(
                    400, 'Weight must be a positive decimal number'
                )
        self.weight = weight

    def is_course_staff(self):
        # pylint: disable=no-member
        """
         Check if user is course staff.
        """
        return getattr(self.xmodule_runtime, 'user_is_staff', False)

    def show_staff_grading_interface(self):
        """
        Return if current user is staff and not in studio.
        """
        in_studio_preview = self.scope_ids.user_id is None
        return self.is_course_staff() and not in_studio_preview


def _resource(path):  # pragma: NO COVER
    """
    Handy helper for getting resources from our kit.
    """
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


def _now():
    """
    Get current date and time.
    """
    return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


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
