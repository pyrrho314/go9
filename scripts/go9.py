#!/usr/bin/env python
import os,sys
import json
import argparse
from go9util import partlocator
from go9util.ksutil import dict2pretty
def err(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
error = err
    
info = err

class Config(object):
    _cfg_dict = None
    filename = None
    cliargs = None
    def __init__(self, cfgdict, cmdline_args = None):
        cliargs = cmdline_args
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
        self.cliargs = cliargs
        
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

class Go9Command(object):
    go9dict = None
    userhome = None
    cfg1 = None
    cfg2 = None
    paths = None
    # cmddict filled near cmd functions, see below
    cmddict = {}
    def __init__(self, config):
        
        bashlines = []
        exportlines = []

        go9cfg = None
        pathslist = []

        
        # info(config.pretty()) 
        self.config = config
        self.paths = paths = config.get("paths")
        self.go9dict = dct = {}
        for pth in paths:
            pthi = 0
            goname = pth["go_name"]
            if goname in dct:
                pthi += 1
            if pthi >0:
                goname += ".%d" %pthi
                
            dct[goname] = pth

    def do_cmd(self, cmd = None, targ = None):
        paths  = self.paths
        dct    = self.go9dict
        config = self.config
        
        cmdlist = self.cmddict.keys()
        
        if cmd in cmdlist:
            cmddef = self.cmddict[cmd]
            if not isinstance(cmddef, dict):
                cmddef = {"function": cmddef}
            
            cmddef["function"](self, cmd, targ)
        else:
            error("No such command: %s" % cmd)
    def add(self, cmd,targ):
        dct = self.cmddict
        paths = self.paths
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
    cmddict["add"] = {"function": add,
                        "help": """
go9 add <dir_key>
    Used to add current directory
                        """.strip()
                      }
    def delete(self, cmd, targ):
        dct = self.cmddict
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
    cmddict["delete"] = {"function": delete,
                        "help": """
go9 delete <dir_key>
    Used to delete a directory from the go table.
                        """.strip()
                      }
    
    def editall(self, cmd, targ):
        dct = self.cmddict
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
    cmddict["editall"] = {"function":editall,
                            "subcmds": ["recurse"],
                            "help": """
go9 editall [recurse]
    Used to edit all appropriate file types. If recurse present, go 
    through sub-directories.  Currently the file types and editor
    is hardcoded. TODO: set edit command and extensions in .go9 config.
                                 """.strip()
                            }
     
    def exportdirs(self, cmd, targ):
        dct = self.go9dict
        targs = dct.keys()
        for targx in targs:
            targx = targx.replace(".","_")
            print "export GO9DIR_{targ}={path};".format(targ=targx, path=dct[targx]["path"])
    cmddict["exportdirs"] = {"function": exportdirs,
                             "help":"""
go9 exportdirs
    Used to create bash environment variables for each go9 
    directory. The vars are of the form GO9DIR_<dir_key>.
                                    """.strip()
                            }
    def help(self, cmd, targ):
        if targ in self.cmddict:
            cd = self.cmddict[targ]
            if "help" in cd:
                info(cd["help"])
            else:
                info ("Sorry, no info on '%s'" % targ)
        else:
            info("go9 commands")
            cmds = self.cmddict.keys()
            cmds.sort()
            info("\t%s" % "\n\t".join(cmds))
    cmddict["help"] = {"function":help,
                       "help": """
go9 help <go9_cmd>
    Used to get information about the commands in go9 tool.

                        """.strip()
                       }
    
    def go(self, cmd, targ):
        dct = self.go9dict
        if targ == None:
            self.do_cmd("list")
        elif targ in dct:
            print "cd %s" % dct[targ]["path"]
        else:
            print 'echo \"No go_name == {targ}\"'.format(targ=targ)
    cmddict["go"] = {"function": go,
                    "help": """
go9 go <dir_key>
go <dir_key>
    Used to change to a target directory. If <dir_key> is
    absent, all targets will be listed.
                            """.strip()
                    }
    def gotargets(self, cmd, targ):
        dct = self.go9dict
        targs = dct.keys()
        targs.sort()
        if targ == "export":
            print " ".join(targs)
        else:
            for targstr in targs:
                print "echo \"%s\";\n" % targstr
    cmddict["gotargets"] = gotargets
    
    def list(self, cmd, targ):
        dct = self.go9dict
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
    cmddict["list"] = list

    def listcmds(self, cmd, targ):
        autocmds = self.cmddict.keys()
        cmds = []
        cmds.extend(autocmds)
        if targ == "export":
            print " ".join(cmds)
        else:
            for cmdstr in cmds:
                print "echo \"%s\";\n" % cmdstr
    cmddict["listcmds"] = listcmds
    
    def listsubcmds(self, cmd, targ):
        if targ in self.cmddict:
            subcmds = None
            cmdict = self.cmddict[targ]
            if isinstance(cmdict, dict):
                subcmds = cmdict["subcmds"] if "subcmds" in cmdict else None
            
            if self.config.cliargs.export:
                if subcmds and len(subcmds) > 0:
                    print " ".join(subcmds)
            else:
                if subcmds and len(subcmds) > 0:
                    print 'echo "%s"' % " ".join(subcmds)
            
    cmddict["listsubcmds"] = { "function": listsubcmds
                            }
        
    def rmturds(self, cmd, targ):
        from glob import glob
        junk = " ".join(glob("*~"))
        print 'rm {junk}'.format(junk = junk)
    cmddict["rmturds"] = rmturds
    
    def rundircmd(self, cmd, targ):
        pass
    cmddict["rundircmd"] = rundircmd
    
    def saverun_cmd(self, cmd, targ):
        import subprocess
        outbuff = ''
        dct = self.go9dict
        # get's previous command and trims it.
        # How lastcmd works:
        #   get history of 2 steps, cut off the history #, 
        
        lastcmd  = 'history 2 | cut -d " " -f 3- | head -n 1 | sed -e "s/^[[:space:]]*//g" -e "s/[[:space:]]*\$//g"'
        outbuff = '_GO9_lastcmd="$({lastcmd})"\n'.format(lastcmd=lastcmd)
        outbuff += (
'''read -p "Use '$_GO9_lastcmd' (y/n)?" choice
case "$choice" in
   y|Y ) 
        go9 set_dir_cmd "$_GO9_lastcmd";;
   n|N )
        echo "Ok nvm.";;
   "" ) echo "what?";;
   * ) 
        echo "other";;
esac

''')
                    
        print outbuff

    cmddict["saverun"] = saverun_cmd
    
    def refresh_cmd(self, cmd,targ):
        print 'GO9_go_targets="$(go9.py gotargets export)"'
        self.do_cmd("exportdirs")
    cmddict["refresh"] = refresh_cmd
    
    # some commands want other commands as targets... for autocomplete
    cmddict["help"]["subcmds"] = cmddict.keys()
    cmddict["listsubcmds"]["subcmds"] = cmddict.keys()
    
# set up parser for command line options

parser = argparse.ArgumentParser(description="Helper for go9 environment.")
parser.add_argument("cmd", default=None, nargs = "?",
                    help="Path(s) to recurse for targets.")
parser.add_argument("target", default=None, nargs = "?",
                    help="The target of the command")
parser.add_argument("-x", "--export", default=False, action="store_true",
                    help="triggers the 'export' mode for some commands"
                    )
parser.add_argument("--config", default=None, 
                    help="Config file to load")

args = parser.parse_args()


# command, targ and default command
cmd = args.cmd if args.cmd else "list"
targ = args.target

# check multiple files
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
        "NO CONFIG\n"
        "  place a .go9 file in $HOME or go9.conf in $HOME/.config")

try:
    #  info("loading %s" % configname)
    config = Config(configname, cmdline_args = args)
except:
    #Exception("Can't Load %s" % configname)
    err("Can't Load %s" % configname)
    raise


go9cmd = Go9Command(config);
        
go9cmd.do_cmd(cmd, targ)
