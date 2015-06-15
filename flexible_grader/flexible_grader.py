"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
import logging

from django.template import Context, Template

from xblock.core import XBlock
from xblock.fields import Scope, Float, String
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

    def student_view(self, context=None):
        """
        The primary view of the FlexibleGradingXBlock, shown to students
        when viewing courses.
        """
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

    def studio_view(self, context=None):
        try:
            cls = type(self)

            def none_to_empty(x):
                return x if x is not None else ''

            edit_fields = (
                (field, none_to_empty(getattr(self, field.name)), validator)
                for field, validator in (
                    (cls.display_name, 'string'),
                    (cls.points, 'number')
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

    @XBlock.json_handler
    def save_flexible_grader(self, data, suffix=''):
        for name in ('display_name', 'points'):
            setattr(self, name, data.get(name, getattr(self, name)))


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
