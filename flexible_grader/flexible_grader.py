"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources

from django.template import Context, Template

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String
from xblock.fragment import Fragment


class FlexibleGradingXBlock(XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    has_score = True
    icon_class = 'problem'

    display_name = String(
            default="Flexible Grading Block", scope=Scope.settings,
            help="Flexible Grading help."
    )

    points = Integer(
        display_name="Maximum score",
        help=("Maximum grade score given to assignment by staff."),
        default=100,
        scope=Scope.settings
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # TO-DO: change this view to display your data your own way.
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
        fragment.add_css(self.resource_string("static/css/flexible_grader.css"))
        fragment.add_javascript(self.resource_string("static/js/src/flexible_grader.js"))
        fragment.initialize_js('FlexibleGradingXBlock')
        return fragment

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("FlexibleGradingXBlock",
             """<vertical_demo>
                <flexible_grader/>
                <flexible_grader/>
                <flexible_grader/>
                </vertical_demo>
             """),
        ]


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