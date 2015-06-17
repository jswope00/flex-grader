/* Javascript for FlexibleGradingXBlock. */
function FlexibleGradingXBlock(runtime, element) {
    function xblock($, _) {
        var getStaffGradingUrl = runtime.handlerUrl(element, 'get_staff_grading_data');
        var enterGradeUrl = runtime.handlerUrl(element, 'enter_grade');
        var removeGradeUrl = runtime.handlerUrl(element, 'remove_grade');
        var template = _.template($(element).find("#sga-tmpl").text());
        var gradingTemplate;

        function render(state) {
            // Render template
            var content = $(element).find("#sga-content").html(template(state));
        }

        function renderStaffGrading(data) {
            $(".grade-modal").hide();

            if (data.display_name !== '') {
                $('.sga-block .display_name').html(data.display_name);
            }

            // Render template
            $(element).find("#grade-info")
                .html(gradingTemplate(data))
                .data(data);

            // Map data to table rows
            data.assignments.map(function(assignment) {
                $(element).find("#grade-info #row-" + assignment.module_id)
                    .data(assignment);
            });

            // Set up grade entry modal
            $(element).find(".enter-grade-button")
                .leanModal({closeButton: "#enter-grade-cancel"})
                .on("click", handleGradeEntry);
        }

        function handleGradeEntry() {
            var row = $(this).parents("tr");
            var form = $(element).find("#enter-grade-form");
            $(element).find("#student-name").text(row.data("fullname"));
            form.find("#module_id-input").val(row.data("module_id"));
            form.find('#submission_id-input').val(row.data('submission_id'));
            form.find("#grade-input").val(row.data("score"));
            form.find("#comment-input").val(row.data("comment"));
            form.off("submit").on("submit", function(event) {
                var max_score = row.parents("#grade-info").data("max_score");
                var score = Number(form.find("#grade-input").val());
                event.preventDefault();
                if (isNaN(score)) {
                    form.find(".error").html("<br/>Grade must be a number.");
                } 
                else if (score !== parseInt(score)) {
                    form.find('.error').html('<br/>Grade must be an integer.');
                }
                else if (score < 0) {
                    form.find(".error").html("<br/>Grade must be positive.");
                }
                else if (score > max_score) {
                    form.find(".error").html("<br/>Maximum score is " + max_score);
                }
                else {
                    // No errors
                    $.post(enterGradeUrl, form.serialize())
                        .success(renderStaffGrading);
                }
            });
            form.find("#remove-grade").on("click", function() {
                var url = removeGradeUrl + '?module_id=' +
                    row.data('module_id') + '&student_id=' +
                    row.data('student_id');
                $.get(url).success(renderStaffGrading);
            });
            //form.find('#enter-grade-cancel').on('click', function() {
            //    /* We're kind of stretching the limits of leanModal, here,
            //     * by nesting modals one on top of the other.  One side effect
            //     * is that when the enter grade modal is closed, it hides
            //     * the overlay for itself and for the staff grading modal,
            //     * so the overlay is no longer present to click on to close
            //     * the staff grading modal.  Since leanModal uses a fade out
            //     * time of 200ms to hide the overlay, our work around is to
            //     * wait 225ms and then just "click" the 'Grade Submissions'
            //     * button again.  It would also probably be pretty
            //     * straightforward to submit a patch to leanModal so that it
            //     * would work properly with nested modals.
            //     *
            //     * See: https://github.com/mitodl/edx-sga/issues/13
            //     */
            //    setTimeout(function() {
            //        $('#grade-submissions-button').click();
            //    }, 225);
            //});
        }

        $(function($) { // onLoad
            var block = $(element).find(".sga-block");
            var state = block.attr("data-state");
            render(JSON.parse(state));

            var is_staff = block.attr("data-staff") == "True";
            if (is_staff) {
                gradingTemplate = _.template(
                    $(element).find("#sga-grading-tmpl").text());
                block.find("#grade-submissions-button")
                    .leanModal()
                    .on("click", function() {
                        $.ajax({
                            url: getStaffGradingUrl,
                            success: renderStaffGrading
                        });
                    });
                block.find('#staff-debug-info-button')
                    .leanModal();
            }
        });
    }

    xblock($, _);
}
