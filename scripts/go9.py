#!/usr/bin/env python
import os,sys
import json
import argparse
from go9util import partlocator
from go9util.ksutil import dict2pretty
def err(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    
info = err

class Config(object):
    _cfg_dict = None
    filename = None
    def __init__(self, cfgdict):
        try:
            if isinstance(cfgdict, basestring):
                self.filename = cfgdict
                cfd = open(cfgdict)
                configdict = json.load(cfd)
                cfd.close()
                self._cfg_dict = configdict
            else:
                self._cfg_dict = cfgdict
        except:
            self._cfg_dict = {"paths":[]}
                #info(dict2pretty("_cfg_dict", self._cfg_dict))
        
    def get(self, key):
        return partlocator.get_property(self._cfg_dict, key)
  
    def set(self, key, val):
        partlocator.set_property(self._cfg_dict, key, val)
        return self

    def pretty(self):
        return dict2pretty("config", self._cfg_dict)

    
    def save(self):
        if self.filename:
            fd = open(self.filename, "w")
            json.dump(self._cfg_dict, fd, indent=4, sort_keys=True)
            fd.close()
        else:
            sys.stderr("Can't Save, no filename\n")


parser = argparse.ArgumentParser(description="Helper for go9 environment.")
parser.add_argument("cmd", default=None, nargs = "?",
                    help="Path(s) to recurse for targets.")
parser.add_argument("target", default=None, nargs = "?",
                    help="The target of the command")
parser.add_argument("--config", default=None, 
                    help="Config file to load")
                    
args = parser.parse_args()

bashlines = []
exportlines = []

go9cfg = None
pathslist = []

userhome   = os.path.expanduser("~")
check1     = os.path.join(userhome,".config/go9.conf")
check2     = os.path.join(userhome,".go9")
configname = None
config = None

if args.config != None:
    configname = args.config
elif os.path.exists(check1):
    configname = check1
elif os.path.exists(check2):
    configname = check2
else:
    raise Exception(
        "NO ARGUMENTS, NO CONFIG\n"
        "  place a .go9 file in $HOME or go9.conf in $HOME/.config")

try:
    #  info("loading %s" % configname)
    config = Config(configname)
except:
    #Exception("Can't Load %s" % configname)
    err("Can't Load %s" % configname)
    raise

cmd = args.cmd if args.cmd else "list"
targ = args.target


# info(config.pretty()) 
paths = config.get("paths")
dct = {}
for pth in paths:
    dct[pth["go_name"]] = pth

def do_cmd(cmd = None, targ = None):
    global paths, dct
    
    if cmd == "add":
        if targ:
            dct = { "go_name": targ,
                    "path": os.getcwd(),
                    "type": "file_system"
                  }
            paths.append(dct)
            # info(dict2pretty("gpy111: paths", paths))
            config.save()
        else:
            err("No target name!")
    elif cmd == "go":
        if targ == None:
            do_cmd("list")
        elif targ in dct:
            print "cd %s" % dct[targ]["path"]
        else:
            print 'echo "No go_name == %s"' % targ
    elif cmd == "list":
        keys = dct.keys()
        keys.sort()
        for key in keys:
            print 'echo "{key} ==> {path}";\n'.format(key=key, path=dct[key]["path"])

do_cmd(cmd, targ)
