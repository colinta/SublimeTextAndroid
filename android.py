import re

import sublime
import sublime_plugin


CLASSES = {
    'ActionBar': 'android.app.ActionBar',
    'Activity': 'android.app.Activity',
    'AlertDialog': 'android.app.AlertDialog',
    'ArrayAdapter': 'android.widget.ArrayAdapter',
    'ArrayList': 'java.util.ArrayList',
    'Build': 'android.os.Build',
    'Bundle': 'android.os.Bundle',
    'Button': 'android.widget.Button',
    'CheckBox': 'android.widget.CheckBox',
    'CompoundButton': 'android.widget.CompoundButton',
    'Configuration': 'android.content.res.Configuration',
    'Context': 'android.content.Context',
    'Date': 'java.util.Date',
    'DateFormat': 'java.text.DateFormat',
    'DialogInterface': 'android.content.DialogInterface',
    'Editable': 'android.text.Editable',
    'EditText': 'android.widget.EditText',
    'Fragment': 'android.app.Fragment',
    'FragmentManager': 'android.app.FragmentManager',
    'Gravity': 'android.view.Gravity',
    'ImageButton': 'android.widget.ImageButton',
    'Intent': 'android.content.Intent',
    'Intent': 'android.content.Intent',
    'LayoutInflater': 'android.view.LayoutInflater',
    'LayoutParams': 'android.widget.LinearLayout.LayoutParams',
    'LinearLayout': 'android.view.LinearLayout',
    'ListFragment': 'android.app.ListFragment',
    'ListView': 'android.widget.ListView',
    'Log': 'android.util.Log',
    'Menu': 'android.view.Menu',
    'MenuInflater': 'android.view.MenuInflater',
    'MenuItem': 'android.view.MenuItem',
    'OnCheckedChangeListener': 'android.widget.CompoundButton.OnCheckedChangeListener',
    'OnClickListener': 'android.view.View.OnClickListener',
    'OnInitListener': 'android.speech.tts.TextToSpeech.OnInitListener',
    'RelativeLayout': 'android.widget.RelativeLayout',
    'SimpleDateFormat': 'java.text.SimpleDateFormat',
    'TextToSpeech': 'android.speech.tts.TextToSpeech',
    'TextView': 'android.widget.TextView',
    'TextWatcher': 'android.text.TextWatcher',
    'Toast': 'android.widget.Toast',
    'UUID': 'java.util.UUID',
    'View': 'android.view.View',
    'ViewGroup': 'android.view.ViewGroup',
    'ViewPager': 'android.support.v4.view.ViewPager',
}


class AndroidAddImportsCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        line_regions = self.view.lines(sublime.Region(0, self.view.size()))
        imports = set()
        classes = set()
        final_point = None
        insert_point = None
        was_package = None
        for region in line_regions:
            line = self.view.substr(region)
            import_match = re.search(r'^import (\w+\..*);', line)
            if import_match:
                if insert_point is None:
                    insert_point = region.a
                # add 1 to select the newline
                final_point = region.b + 1

                imports |= {import_match.group(1),}
            else:
                for class_name in CLASSES.keys():
                    for class_match in re.finditer(r'\b{0}\b'.format(class_name), line):
                        classes |= {CLASSES[class_match.group(0)],}

            if insert_point is None and not was_package:
                empty_line_match = re.search(r'^$', line)
                if empty_line_match:
                    insert_point = region.a
                    final_point = region.b

            was_package = bool(re.search(r'^package', line))

        to_import = list(classes | imports)
        new_imports = classes - imports
        to_import.sort()

        if len(to_import):
            msg = ''
            for stmt in new_imports:
                if len(msg):
                    msg += ', '
                msg += stmt
            sublime.status_message('Adding: ' + msg)

            to_import_stmt = map(lambda stmt: "import " + stmt + ";\n", to_import)

            to_insert = ''
            insert_region = sublime.Region(insert_point, final_point)

            for import_stmt in to_import_stmt:
                to_insert += import_stmt

            self.view.replace(edit, insert_region, to_insert)


class AndroidGenerateSettersCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        line_regions = self.view.lines(sublime.Region(0, self.view.size()))

        to_add = []
        getters = []
        setters = []
        index = 0
        last_line = None
        for region in line_regions:
            line = self.view.substr(region)
            attr_match = re.search(r'^([ \t]+)(private|public) ((?!class)\w+(?:\[\])?) [m_]?(\w+)\b(?!\()', line)
            getter_match = re.search(r'^[ \t]+(private|public) (\w+(?:\[\])?) get([A-Z]\w*)\b(?=\()', line)
            setter_match = re.search(r'^[ \t]+(private|public) (\w+(?:\[\])?) set([A-Z]\w*)\b(?=\()', line)
            last_line_match = re.search(r'^}', line)

            if last_line_match:
                last_line = region.a
            elif attr_match:
                ws = attr_match.group(1)
                scope = attr_match.group(2)
                varclass = attr_match.group(3)
                varname = attr_match.group(4)
                entry = {
                    'scope': scope,
                    'whitespace': ws,
                    'varclass': varclass,
                    'varname': varname,
                    'getter': True,
                    'setter': True,
                    'index': index
                }
                index += 1
                to_add.append(entry)
            elif getter_match:
                text = getter_match.group(3)
                varname = text[0].lower() + text[1:]
                getters.append(varname)
            elif setter_match:
                text = setter_match.group(3)
                varname = text[0].lower() + text[1:]
                setters.append(varname)

        will_add = []
        for entry in to_add:
            for text in getters:
                if entry['varname'] == text:
                    entry['getter'] = False
            for text in setters:
                if entry['varname'] == text:
                    entry['setter'] = False

            if entry['getter'] or entry['setter']:
                will_add.append(entry)

        will_add.sort(key=lambda entry: -entry['index'])
        for entry in will_add:
            ws = entry['whitespace']
            varclass = entry['varclass']
            varname = entry['varname']
            ucfirst = varname[0].upper() + varname[1:]
            if entry['getter']:
                getter = '{ws}public {varclass} get{ucfirst}() {{ return _{varname}; }}\n'.format(varclass=varclass, varname=varname, ucfirst=ucfirst, ws=ws, tab='    ')
                self.view.replace(edit, sublime.Region(last_line, last_line), getter)
            if entry['setter']:
                setter = '{ws}public {varclass} set{ucfirst}({varclass} {varname}) {{ _{varname} = {varname}; }}\n'.format(varclass=varclass, varname=varname, ucfirst=ucfirst, ws=ws, tab='    ')
                self.view.replace(edit, sublime.Region(last_line, last_line), setter)

