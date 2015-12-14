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
    elif cmd == "editall":
        from glob import glob
        jss   = " ".join(glob("*.js"))
        htmls = " ".join(glob("*.html"))
        pys   = " ".join(glob("*.py"))
        shs   = " ".join(glob("*.sh"))
        print 'ne {jss} {htmls} {pys} {shs}'.format(
                jss=jss, htmls=htmls, pys = pys, shs = shs)
    elif cmd == "exportdirs":
        targs = dct.keys()
        for targx in targs:
            print "export GO9DIR_{targ}={path};".format(targ=targx, path=dct[targx]["path"])
    elif cmd == "go":
        if targ == None:
            do_cmd("list")
        elif targ in dct:
            print "cd %s" % dct[targ]["path"]
        else:
            print 'echo \"No go_name == {targ}\"'.format(targ=targ)
    elif cmd == "gotargets":
        targs = dct.keys()
        targs.sort()
        if targ == "export":
            print " ".join(targs)
        else:
            for targstr in targs:
                print "echo \"%s\";\n" % targstr
    elif cmd == "list":
        keys = dct.keys()
        keys.sort()
        maxkeylen = len(max(keys, key= lambda p: len(p)))+1
        keyfrag = "{key: >%d}" % maxkeylen
        for key in keys:
            formstr = 'echo "%s ==> {path}";\n' % keyfrag
            print formstr.format(
                            key=key, path=dct[key]["path"])
    elif cmd == "listcmds":
        cmds = ["add",
                "go",
                "editall",
                "exportdirs",
                "gotargets",
                "list",
                "listcmds",
                "rmturds"]
        if targ == "export":
            print " ".join(cmds)
        else:
            for cmdstr in cmds:
                print "echo \"%s\";\n" % cmdstr
    elif cmd == "rmturds":
        from glob import glob
        junk = " ".join(glob("*~"))
        print 'rm {junk}'.format(junk = junk)
        
do_cmd(cmd, targ)
