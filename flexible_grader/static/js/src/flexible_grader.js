/* Javascript for FlexibleGradingXBlock. */
function FlexibleGradingXBlock(runtime, element) {
    function xblock($, _) {
        var getStaffGradingUrl = runtime.handlerUrl(element, 'get_staff_grading_data');
        var enterGradeUrl = runtime.handlerUrl(element, 'enter_grade');
        var enterBulkGradeUrl = runtime.handlerUrl(element, 'enter_bulk_grade');
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
                .leanModal({
                    closeButton: "#enter-grade-cancel"
                })
                .on("click", handleGradeEntry);

            $(element).find("#enter-bulk-grade-button")
                .leanModal({
                    closeButton: "#enter-grade-cancel"
                })
                .on("click", handleBulkGradeEntry);

            $(element).find("#select-all")
                .change(selectAll)

            $(element).find(".singles")
                .change(handleSingleSelection)
        }

        function handleSingleSelection() {
            var checkboxes = $(this).closest('table').find(':checkbox');
            var anyUnchecked = checkboxes.not(':checked,#select-all').length;
            if (anyUnchecked > 0) {
                $(element).find("#select-all").prop('checked', false);
            } else {
                $(element).find("#select-all").prop('checked', true);
            }

            var checkedCheckboxes = $(this).closest('table').find(':checkbox:checked');
            if (checkedCheckboxes.length > 1) {
                $(element).find("#bulk-grade").show();
            } else {
                $(element).find("#bulk-grade").hide();
            }
        }

        function selectAll() {
            var checkboxes = $(this).closest('table').find(':checkbox');
            if ($(this).is(':checked')) {
                checkboxes.prop('checked', true);
            } else {
                checkboxes.prop('checked', false);
            }

            var checkedCheckboxes = $(this).closest('table').find(':checkbox:checked');
            if (checkedCheckboxes.length > 1) {
                $(element).find("#bulk-grade").show();
            } else {
                $(element).find("#bulk-grade").hide();
            }
        }

        function handleGradeEntry() {
            var row = $(this).parents("tr");
            var form = $(element).find("#enter-grade-form");
            $(element).find("#student-name").text(row.data("fullname"));
            $("#grade-for").show();
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
                } else if (score !== parseInt(score)) {
                    form.find('.error').html('<br/>Grade must be an integer.');
                } else if (score < 0) {
                    form.find(".error").html("<br/>Grade must be positive.");
                } else if (score > max_score) {
                    form.find(".error").html("<br/>Maximum score is " + max_score);
                } else {
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

        function handleBulkGradeEntry() {
            $("#grade-for").hide();
            $("#comment-input").val('');
            $("#grade-input").val('');

            var table = $(element).find("#grading-table");
            var rows = table.find("tr").not(":first");
            var form = $(element).find("#enter-grade-form");
            var studentData = [];
            var i;

            var selectedRows = rows.filter(function(i, e) {
                return $(':checkbox:checked', this).length > 0;
            });

            for (i = 0; i < selectedRows.length; i++) {
                var row = $(selectedRows[i]);
                studentData.push({
                    module_id: row.data("module_id"),
                    submission_id: row.data("submission_id")
                });
            }

            form.off("submit").on("submit", function(event) {
                var max_score = row.parents("#grade-info").data("max_score");
                var score = Number(form.find("#grade-input").val());
                event.preventDefault();
                if (isNaN(score)) {
                    form.find(".error").html("<br/>Grade must be a number.");
                } else if (score !== parseInt(score)) {
                    form.find('.error').html('<br/>Grade must be an integer.');
                } else if (score < 0) {
                    form.find(".error").html("<br/>Grade must be positive.");
                } else if (score > max_score) {
                    form.find(".error").html("<br/>Maximum score is " + max_score);
                } else {
                    // No errors
                    var data = {
                        grade: $("#grade-input").val(),
                        comment: $("#comment-input").val(),
                        students: JSON.stringify(studentData)
                    };

                    $.post(enterBulkGradeUrl, $.param(data))
                        .success(renderStaffGrading);
                }
            });
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
