from . import termcolor as tc
from . import partlocator
from pprint import pprint,pformat
Error = Exception


class KSUtilError(Error):
    msg = "error in ksutil.py"

def calc_fulltab(indent):
    tabspc = " "*4
    fulltab = tabspc*indent
    return fulltab

def dict2pretty(name, var, indent=0, namewidth = None, complete = False, say_type = None):
    #retstr = pformat(var)
    retstr = u""
    fulltab = calc_fulltab(indent)
    tabspc  = calc_fulltab(1)
    _o_namewidth = namewidth
    if not namewidth:
        namewidth = len(str(name))
    if isinstance(var, dict):
        retstr += "\n%(indent)s%(key)s %(type)s:" % {
                                                    "indent":fulltab,
                                                    "key": tc.colored(name, attrs=["bold"]),
                                                    "type": tc.colored(repr(type(var)), attrs=["dark"]),
                                                    "extra": tabspc
                                                 }
        sub_namewidth = maxkeylen(var)
        # "ks19: sub_nw=", sub_namewidth
        if len(var) == 0:
            retstr += "\n%(indent)s%(tab)s:::empty:::" % {"indent":fulltab,
                                                          "tab":tabspc
                                                          }
        keys = var.keys()
        keys.sort()
        for key in keys:
            value = var[key]
            # key,value
            newstr = dict2pretty(key, value, indent+1, namewidth = sub_namewidth )
            # "ks28: indent =", indent, namewidth, _o_namewidth
            # "ks31: newstr", newstr
            retstr += newstr
            
    elif isinstance(var, list):
         retstr += "\n%(indent)s%(key)s %(type)s:" % { "indent":fulltab,
                                                    "key": tc.colored(name, attrs=["bold"]),
                                                    "type": tc.colored(repr(type(var)), attrs=["dark"]),
                                               }
         
         listlen = len(var)
         
         if len(var) < 50:
             allstr = True
             reprline = []
             for v in var:
                reprline.append( repr(v))
                if not isinstance(v, str):
                    allstr = False
             if allstr:
                oneline = ", ".join(var)
             else:
                oneline = ", ".join(reprline)
             if len(oneline)<120:
                return dict2pretty(name, oneline, indent, say_type = type(var), namewidth = namewidth)
                   
         if listlen > 10 and not complete == True:
            last = listlen - 1
            mid = int(last/2);
            retstr += dict2pretty("[0]", var[0], indent+1, namewidth = namewidth) 
            retstr += dict2pretty("[%d]"%mid, var[mid],indent+1, namewidth = namewidth)
            retstr += dict2pretty("[%d]"%last, var[last], indent+1, namewidth = namewidth)  
         else:
            for i in range(0, listlen):
                key = "[%d]"%i
                value = var[i];
                if hasattr(value, "pretty_string"):
                    retstr += tc.colored("\n[%d]" % i, attrs=["bold"])
                    retstr += value.pretty_string(start_indent = indent+1)
                else:     
                    retstr += dict2pretty(key, value, indent+1, namewidth = namewidth)
    else:
        if say_type:
            stype = repr(say_type)
        else:
            vtype = type(var)
            if vtype.__name__ not in dir(__builtins__):
                stype ="<object>"
                stype = repr(type(var))
            else: 
                stype = repr(type(var))
            
        if isinstance(var, str):
            pvar = var.strip()
        else:
            pvar = repr(var)
  
        retstr += "\n%(indent)s%(key)s =  %(val)s  %(type)s" % {
                                                        "indent": fulltab,
                                                        "key": tc.colored(
                                                                _pad_str(name, namewidth)
                                                                , attrs=["bold"]),
                                                        "type": tc.colored(
                                                                  _pad_str(stype, len(stype)), attrs=["dark"]),
                                                        "val": unicode(_pad_str(pvar,20), errors="replace")
                                                       }
    if indent == 0:
        retstr = retstr.strip()
    return retstr

from collections import defaultdict

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.iteritems():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def xml_dict_load(filename):
    import xml.etree.ElementTree as ET
    tree = ET.parse(filename)
    dic = etree_to_dict(tree.getroot())
    return dic

def xml_dict_parse(xmltxt):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xmltxt)
    dic = etree_to_dict(root)
    return dic
        

def maxkeylen (d):
    keys = d.keys()
    kl = 0
    for key in keys:
        keylen = len(str(key))
        if keylen>kl:
            kl = keylen
    return kl
            
def _pad_str(tstr, length):
    tstr = str(tstr)
    slen = len(tstr)
    pad = " " * (length-slen)
    return tstr+pad

def context_args(context_args):
    """Converts a user supplied list in the format returned by argparse
    e.g. [["a","=","100"],["a=datetime.now()"]]]
    
    The list is turned into a single line, the result split by "=". No equals
    means set the arg to True.  The value is eval-ed.
    """
    d = {}
    # "r25:", argl, argv
    if context_args:
        from datetime import datetime, date, timedelta
        for item in context_args:
            # "r27:",item
            expr = "".join(item)
            if  "=" in expr:
                lrval  = expr.split("=")
                lval = lrval[0]
                if len(lrval)>1:
                    theval = eval(lrval[1])
                else:
                    theval = True
                d[lval] = theval
            else:
                if   len(item) == 2:
                    thekey = item[0]
                    theval = eval(item[1])
                    d[thekey] = theval
                elif len(item) == 1:
                    d[item[0]] = True
                    
    return d

# debugging help
# NOTE: uses inspect... might slow down inner loops
def lineno():
    import inspect
    return inspect.currentframe().f_back.f_lineno
    
def called_me(extra_frame = 0):
    import inspect
    (frame, 
    filename, line_number, 
    function_name, lines, 
    index) = inspect.getouterframes(inspect.currentframe())[2+extra_frame]
    fi = {
        "frame":         frame,
        "filename":      filename,
        "line_number":   line_number,
        "function_name": function_name,
        "lines":         lines,
        "index":         index
        }
    return fi
       
def str2pytype(value, pytype = None):
    retval = None
    if pytype == bool:
        if type(value) == str:
            if (value.lower() == "true"):
                retval = True
            elif (value.lower() == "false"):
                retval = False
            else:
                mes = "%s is not legal boolean setting " % value
                mes += 'for "boolean %s"' % parmname
                raise KSUtilError(mes)
        else:
            retval = pytype(value)  
    else:
        retval = pytype(value)
    return retval         
    
def iter_date(start_date, end_date):
    from datetime import timedelta
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

from random import sample
from string import digits, ascii_uppercase, ascii_lowercase
from tempfile import gettempdir
from os import path

def rand_file_id(length=12):
    chars = ascii_lowercase + ascii_uppercase + digits

    fname = ''.join(sample(chars, length))

    return fname 

def keysWithoutUnderscore(nDict):
    keys = filter(lambda item: not isinstance(item, str) and not item.startsWith("_"), nDict.keys())
    return keys;

def dirReport (path2goDict, cwdkey):
    cwdkeyParts = cwdkey.split(".")
    parentkeyParts = cwdkey[:-1]
    parentkey = ".".join(parentKeyParts)
    parentDict = partlocator.get_property(path2goDict, parentkey)
    cwdDict = partlocator.get_property(path2goDict, cwdkey)
    return {
        "siblings": keysWithoutUnderscore(parentDict),
        "children": keysWithoutUnderscore(cwdDict)
    }
    
    
def publicKeys( obarg):
    ''' Just return object keys not starting with _
    '''
    if (obarg):
        cleanary = filter( lambda x: x and len(x) and x[0] != "_", obarg.keys() )
    else:
        cleanary = None
    
    return list(cleanary)