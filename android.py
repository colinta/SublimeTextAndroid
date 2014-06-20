import re

import sublime
import sublime_plugin


CLASSES = {
    'ActionBar': 'android.app.ActionBar',
    'Activity': 'android.app.Activity',
    'AlertDialog': 'android.app.AlertDialog',
    'Bundle': 'android.os.Bundle',
    'Button': 'android.widget.Button',
    'Configuration': 'android.content.res.Configuration',
    'DialogInterface': 'android.content.DialogInterface',
    'EditText': 'android.widget.EditText',
    'Gravity': 'android.view.Gravity',
    'ImageButton': 'android.widget.ImageButton',
    'Intent': 'android.content.Intent',
    'Intent': 'android.content.Intent',
    'LayoutParams': 'android.widget.LinearLayout.LayoutParams',
    'LinearLayout': 'android.widget.LinearLayout',
    'Log': 'android.util.Log',
    'Menu': 'android.view.Menu',
    'MenuInflater': 'android.view.MenuInflater',
    'MenuItem': 'android.view.MenuItem',
    'OnClickListener': 'android.view.View.OnClickListener',
    'OnInitListener': 'android.speech.tts.TextToSpeech.OnInitListener',
    'RelativeLayout': 'android.widget.RelativeLayout',
    'TextToSpeech': 'android.speech.tts.TextToSpeech',
    'TextView': 'android.widget.TextView',
    'Toast': 'android.widget.Toast',
    'View': 'android.view.View',
}


class AndroidAddImportsCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        line_regions = self.view.lines(sublime.Region(0, self.view.size()))
        imports = set()
        classes = set()
        final_point = None
        insert_point = None
        for region in line_regions:
            line = self.view.substr(region)
            import_match = re.search(r'^import (android\..*);', line)
            if import_match:
                if not insert_point:
                    insert_point = region.a
                final_point = region.b + 1  # add 1 for the newline

                imports |= {import_match.group(1),}
            else:
                for class_name in CLASSES.keys():
                    for class_match in re.finditer(r'\b{0}\b'.format(class_name), line):
                        classes |= {CLASSES[class_match.group(0)],}

        to_import = list(classes | imports)
        new_imports = classes - imports
        to_import.sort()

        if len(to_import) and insert_point:
            msg = ''
            for stmt in new_imports:
                if len(msg):
                    msg += ', '
                msg += stmt
            sublime.status_message('Adding: ' + msg)

            to_import_stmt = map(lambda stmt: "import " + stmt + ";\n", to_import)

            to_insert = ''
            for import_stmt in to_import_stmt:
                to_insert += import_stmt
            self.view.replace(edit, sublime.Region(insert_point, final_point), to_insert)
