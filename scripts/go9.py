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
        
    def get(self, key, default = None):
        retval = partlocator.get_property(self._cfg_dict, key)
        if retval == None:
            return default
        else:
            return retval
  
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
    pthi = 0
    goname = pth["go_name"]
    if goname in dct:
        pthi += 1
    if pthi >0:
        goname += ".%d" %pthi
        
    dct[goname] = pth

def do_cmd(cmd = None, targ = None):
    global paths, dct, config
    
    if cmd == "add":
        curpath = os.getcwd()
        if targ:
            numvers = 0
            for pth in paths:
                if pth["go_name"] == targ:
                    numvers += 1
            if numvers>0:
                info("Already have key '%s'"%targ)
                info("--> %s" % curpath)
            else:
                elemdct =   { 
                            "go_name": targ,
                            "path": curpath,
                            "type": "file_system"
                            }
                paths.append(elemdct)
            # info(dict2pretty("gpy111: paths", paths))
                config.save()
                print 'GO9_go_targets="$(go9.py gotargets export)"'
        else:
            err("No target name!")
    elif cmd == "delete":
        removedone = False
        newlist = []
        rmlist = []
        for onepath in paths:
            tkey = onepath["go_name"]
            if tkey == targ:
                rmlist.append(onepath)
                removedone = True
            else:
                newlist.append(onepath)
        if removedone:
            config.set("paths", newlist)
            rml = config.get("removed_paths", [])
            rml.extend(rmlist)
            config.save()
        print 'GO9_go_targets="$(go9.py gotargets export)"'
    elif cmd == "editall":
        from glob import glob
        Ajss = []
        Ahtmls = []
        Apys = []
        Ashs = []
        Acsss = []
        for root, dirs, files in os.walk("."):
            Ajss  .extend(glob(os.path.join(root, "*.js"  )))
            Ahtmls.extend(glob(os.path.join(root, "*.html")))
            Apys  .extend(glob(os.path.join(root, "*.py"  )))
            Ashs  .extend(glob(os.path.join(root, "*.sh"  )))
            Acsss .extend(glob(os.path.join(root, "*.css" )))
            if targ != "recurse":
                break;
            # prune some directories
            while "node_modules" in dirs:
                dirs.remove("node_modules")
            while "bower_components" in dirs:
                dirs.remove("bower_components")
        
        if len(Ajss) or len(Ahtmls) or len(Apys) or len(Ashs):
            jss = " ".join(Ajss)
            htmls = " ".join(Ahtmls)
            pys = " ".join(Apys)
            shs = " ".join(Ashs)
            
            
            print 'ne {jss} {htmls} {pys} {shs}'.format(
                    jss=jss, htmls=htmls, pys = pys, shs = shs)
        else:
            info ("no appropriate files found")
    elif cmd == "exportdirs":
        targs = dct.keys()
        for targx in targs:
            targx = targx.replace(".","_")
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
            showline = True
            if targ:
                showline = targ in key
            if showline:
                formstr = 'echo "%s ==> {path}";\n' % keyfrag
                print formstr.format(
                                key=key, path=dct[key]["path"])
    elif cmd == "listcmds":
        cmds = ["add",
                "go",
                "delete",
                "editall",
                "exportdirs",
                "gotargets",
                "list",
                "listcmds",
                "saverun",
                "refresh",
                "rmturds"]
        if targ == "export":
            print " ".join(cmds)
        else:
            for cmdstr in cmds:
                print "echo \"%s\";\n" % cmdstr
    elif cmd == "refresh":
        print 'GO9_go_targets="$(go9.py gotargets export)"'
        do_cmd("exportdirs")
    elif cmd == "rmturds":
        from glob import glob
        junk = " ".join(glob("*~"))
        print 'rm {junk}'.format(junk = junk)
    elif cmd == "run_dir_cmd":
        pass
    elif cmd == "saverun":
        # get's previous command and trims it.
        lastcmd = 'history 2 | cut -d " " -f 3- | head -n 3 | sed -e "s/^[[:space:]]*//g" -e "s/[[:space:]]*\$//g"'
        info("Use Last Command? %s" % lastcmd)
        info("[Y,n]:")
        try:
            answer = raw_input()
        except KeyboardInterrupt:
            info("Exit")
        answer = answer.strip()
        if len(answer) == 0 or answer.lower() == "y":
            info("do the command work")
            print "_GO9_lastcmd=$({lastcmd})".format(lastcmd=lastcmd)
        else:
            info("Not saved.")
        
    else:
        info("Unknown command: %s" % cmd)
do_cmd(cmd, targ)
