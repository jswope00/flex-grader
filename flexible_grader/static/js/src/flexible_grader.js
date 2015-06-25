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
            if (data.display_name !== '') {
                $('.sga-block .display_name').html(data.display_name);
            }

            // Render template
            $(element).find("#grade-info")
                .html(gradingTemplate(data))
                .data(data);

            $.unblockUI();

            var table = $(element).find("#grading-table");
            var max_score = table.parents("#grade-info").data("max_score");
            $('.grade-input').each(function() {
                var $this = $(this);

                $this.prop('min', 0);
                $this.prop('max', max_score);
            });

            // Map data to table rows
            data.assignments.map(function(assignment) {
                $(element).find("#grade-info #row-" + assignment.module_id)
                    .data(assignment);
            });

            $(element).find("#submit-grade-button")
                .off()
                .on("click", submitGrade);

            $(element).find(".remove-grade-button")
                .off()
                .on("click", clearGrade);
        }

        function clearGrade() {
            var row = $(this).parents("tr");
            var url = removeGradeUrl + '?module_id=' +
                row.data('module_id') + '&student_id=' +
                row.data('student_id');

            $.blockUI({
                message: $('#sga-loader'),
                baseZ: 11001
            });

            $.get(url).success(renderStaffGrading);
        }

        function submitGrade() {
            var table = $(element).find("#grading-table");
            var rows = table.find("tr").not(":first");
            var studentData = [];
            var missingData = false;
            var i;

            $('.comment-input').each(function() {
                var $this = $(this);

                if ($this.val() != "") {
                    var parentId = $this.data("parent");
                    var parentObj = $("#" + parentId);

                    parentObj.prop('required', true);
                }
            });

            var isValid = true;

            $('.grade-input').each(function() {
                isValid = isValid && this.checkValidity();
            });

            if (!isValid) {
                $(element).find('.error').show();
                return;
            } else {
                $(element).find('.error').hide();
            }

            var selectedRows = table.find('tr')
                .filter(function() {
                    var length = $(this).find('#grade-input-' + this.id + '[value!=""]').length;
                    return length > 0;
                });

            for (i = 0; i < selectedRows.length; i++) {
                var row = $(selectedRows[i]);
                studentData.push({
                    grade: $(".grade-input", row).val(),
                    comment: $(".comment-input", row).val(),
                    module_id: row.data("module_id"),
                    submission_id: row.data("submission_id")
                });
            }

            var data = {
                students: JSON.stringify(studentData)
            };

            $.blockUI({
                message: $('#sga-loader'),
                baseZ: 11001
            });

            $.post(enterGradeUrl, $.param(data))
                .success(renderStaffGrading);
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
                    .leanModal({
                        closeButton: ".modal_close"
                    })
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
