"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
import logging
import json

from courseware.models import StudentModule

from django.template import Context, Template

from webob.response import Response

from xblock.core import XBlock
from xblock.fields import Scope, Float, String, Boolean
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


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
        values={"min":0, "step": .1},
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

    score_published = Boolean(
        display_name="Whether score has been published.",
        help=("This is a terrible hack, an implementation detail."),
        default=True,
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

    def student_view(self, context=None):
        """
        The primary view of the FlexibleGradingXBlock, shown to students
        when viewing courses.
        """
        if not self.score_published:
            self.runtime.publish(self, 'grade', {
                'value': self.score,
                'max_value': self.max_score()
            })
            self.score_published = True

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

        if self.score is not None:
            graded = {'score': self.score, 'comment': self.comment}
        else:
            graded = None

        return {
            "graded": graded,
            "max_score": self.max_score(),
            "published": self.score_published
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

    def staff_grading_data(self):
        def get_student_data(module):
            state = json.loads(module.state)
            return {
                'module_id': module.id,
                'username': module.student.username,
                'email': module.student.email,
                'published': state.get("score_published"),
                'comment': state.get("comment", '')
            }

        query = StudentModule.objects.filter(
            course_id=self.xmodule_runtime.course_id,
            module_state_key=self.location
        )

        return {
            'assignments': [get_student_data(module) for module in query],
            'max_score': self.max_score()
        }

    @XBlock.handler
    def get_staff_grading_data(self, request, suffix=''):
        assert self.is_course_staff()
        return Response(json_body=self.staff_grading_data())

    @XBlock.json_handler
    def save_flexible_grader(self, data, suffix=''):
        for name in ('display_name', 'points', 'weight'):
            setattr(self, name, data.get(name, getattr(self, name)))

    def is_course_staff(self):
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
