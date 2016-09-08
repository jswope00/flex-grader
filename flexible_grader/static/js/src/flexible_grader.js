var import_url =''

/* Javascript for FlexibleGradingXBlock. */
function FlexibleGradingXBlock(runtime, element) {
    function xblock($, _) {
        var getStaffGradingUrl = runtime.handlerUrl(element, 'get_staff_grading_data');
        var enterGradeUrl = runtime.handlerUrl(element, 'enter_grade');
	var enterexportUrl = runtime.handlerUrl(element, 'export_flex_grader');
        var enterimportUrl = runtime.handlerUrl(element, 'import_flex_grader');
        var removeGradeUrl = runtime.handlerUrl(element, 'remove_grade');
        var template = _.template($(element).find("#sga-tmpl").text());
        var errorTemplate = _.template($(element).find("#sga-error-tmpl").text());
        var gradingTemplate;
	import_url = enterimportUrl
	//console.log('import_flex_grader');

        function render(state) {
            // Render template
            var content = $(element).find("#sga-content").html(template(state));
        }

        function renderStaffGrading(data) {
            if (data.hasOwnProperty('error')) {
                $(element).find("#grade-info")
                    .html(errorTemplate(data));

                return;
            }

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
       

	$(element).find("#import_grade_data")
                .off()
                .on("change", importcsv);
 
	$(element).find("#import_grade_button")
                .off()
                .on("click", importcsv_click);
     

        $(element).find("#export_grade_data")
                .off()
                .on("click", exportcsv);


	 }

         function exportcsv()			
 		{
		console.log(enterexportUrl)
	        window.location = enterexportUrl;

		}


	function importcsv()
	{
	//debugger;
	console.log('form submit')
	$('#import_csv_frm').submit()
	}


	function importcsv_click()
	{	$('#import_grade_data').trigger('click');
	
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

            $.get(url)
                .success(function() {
                    $(".grade-input", row).val('');
                    $(".grade-input", row).prop('required', false);

                    $(".comment-input", row).val('');

                    row.find('.sga-score').empty();
                    row.find('.sga-comment').empty();

                    $.unblockUI();
                });

        }

        function submitGrade() {
            var table = $(element).find("#grading-table");
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
                .success(function() {
                    // update the UI
                    selectedRows.each(function() {
                        var $this = $(this);
                        var score = $(".grade-input", $this).val();
                        var comment = $(".comment-input", $this).val();

                        $this.find('.sga-score').html(score);
                        $this.find('.sga-comment').html(comment);

                        $(".grade-input", $this).val('');
                        $(".grade-input", $this).prop('required', false);

                        $(".comment-input", $this).val('');
                    });

                    $.unblockUI();
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
                    .leanModal({
                        closeButton: ".modal_close"
                    })
                    .on("click", function() {
                        $(element).find("#grade-info").empty();

                        $.blockUI({
                            message: $('#sga-loader'),
                            baseZ: 11001
                        });

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


function uploadcsv()
        {
//debugger;

var csv_file = $('#import_grade_data');


        var fileName = csv_file.val();
        var ext = fileName.substring(fileName.lastIndexOf('.') + 1);
	if (ext !='csv')
{

	alert('Please upload CSV file');
return false ;
}

var form = $('#import_csv_frm');
//var myform  = new FormData(form);
var myform  = new FormData();
myform.append('csv_file', $('input[type=file]')[0].files[0]);

 $.blockUI({
                message: $('#sga-loader'),
                baseZ: 11001
            });

$.ajax({
    url: import_url,
    type: 'POST',
    data: myform,
    cache: false,
    processData: false,
    contentType: false,
    success: function(data) {


$.unblockUI();
$('input[type=file]').val('');
if(data.length==0)
{
alert('CSV upload failed. See system admin')
}

else
{
for (var i = 0; i < data.length; i++) { 
console.log(data[i][0])

$('#row-'+data[i][0]).find('.sga-score').html(data[i][1]);
$('#row-'+data[i][0]).find('.sga-comment').html(data[i][2]);

}

alert('CSV upload successful. '+data.length+' entries updated');

}

    }
});

        
        return false
        }
