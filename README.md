# flex-grader
A flexible grading tool for EdX, where you can assign a grade and comment to any member of a course. Use case might be for grading participation. 


Installation
------------

Make sure that `ALLOW_ALL_ADVANCED_COMPONENTS` feature flag is set to `True` in `cms.env.json`.

Get the source to the /edx/app/edxapp/ folder and execute the following command:

```bash
sudo -u edxapp /edx/bin/pip.edxapp install flex-grader/
```

To upgrade an existing installation of this XBlock, fetch the latest code and then type:

```bash
sudo -u edxapp /edx/bin/pip.edxapp install -U --no-deps flex-grader/
```

Enabling in Studio
------------------

You can enable the flex-grader XBlock in studio through the advanced
settings.

1. From the main page of a specific course, navigate to `Settings ->
   Advanced Settings` from the top menu.
2. Check for the `advanced_modules` policy key, and add
   `"flexible_grader"` to the policy value list.
3. Click the "Save changes" button.
