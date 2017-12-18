#!/usr/bin/env python
import os,sys
import json
import argparse
from go9util import partlocator
from go9util.ksutil import dict2pretty

try:
    import blessed
    TERM=blessed.Terminal()
except:
    blessed = None
    TERM=None

def err(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")
error = err
    
info = err

# handling quoted arguments is a pain btwn bash and python...
# by default bash swallows the quotes. In go9.sh we recover
# these using $@, but still by the time go9.py is invoked
# the words in the quotes are all separate arguments. However
# some arguments begin with a quote, and some end with one
# so we go through and recollect these into a single argument
# and go ahead and swallow the quotes used to group the words.
argv = []
j = 0
building = False
for i in range( len(sys.argv)):
    arg = sys.argv[i]
    if arg[0] == '"':
        building = True
        argv.append(arg[1:])
        continue
    if arg[-1] == '"':
        if building:
            argv[-1] += " %s" % arg[:-1]
        else:
            argv.append(arg)
        building = False
        continue
    if building:
        argv[-1] += " %s" % arg
    else:
        argv.append(arg)
#info("go9py14: %s" % str(sys.argv))
sys.argv = argv
#info("go9py14: %s" % str(sys.argv))

        
class Config(object):
    _cfg_dict = None
    filename = None
    cliargs = None
    def __init__(self, cfgdict, cmdline_args = None):
        cliargs = cmdline_args
        try:
            if cfgdict == None:
                self._cfg_dict = self._default_start_dict()
            elif isinstance(cfgdict, basestring):
                self.filename = cfgdict
                cfd = open(cfgdict)
                configdict = json.load(cfd)
                cfd.close()
                self._cfg_dict = configdict
            else:
                self._cfg_dict = cfgdict
        except:
            self._cfg_dict = {self._default_start_dict()}
                #info(dict2pretty("_cfg_dict", self._cfg_dict))
        self.cliargs = cliargs

    def _default_start_dict(self):
        return {"paths":[],
                "spc_cmds": {   "editor": {"command": "nano {files}"},
                                "new_editor": {"command": "nano {files}"}
                            },
                
               }
        
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

    
    def save(self, fn = None):
        if fn:
            self.filename = fn
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
    # cmddict filled after each command function
    # thus declared classwide
    cmddict = {}
    run_dict = None
    
    
    def _get_run_cmds(self):
        rcs = config.get("run_cmds");
        if not rcs:
            rcs = {}
            config.set("run_cmds", rcs)
        return rcs
    run_cmds = property(_get_run_cmds)
    
    def __init__(self, config):
        go9cfg = None
        pathslist = []

        # info(config.pretty()) 
        self.run_dict = {}
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
        # touch up the cmddict to help out some commands
        runcmds = self.run_cmds
        runkeys = runcmds.keys()
        self.cmddict["run"]["subcmds"] = runkeys

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
            for pi in range(len(paths)):
                pth= paths[pi];
                if pth["go_name"] == targ:
                    numvers += 1
                    hittarg = pth
                    hittargindex = pi
            if numvers>1:
                err("config error, multiple targets for 'go_name' {goname}".format(goname=targ))
            if numvers>0:
                info("Already have key '%s' --> %s" % (targ,hittarg['path']))
                if (curpath == hittarg['path']):
                    info("path already set");
                    return
                if not self.config.cliargs.force:
                    err('Use -f flag to force override.')
                    return
                elemdct = {
                            "go_name":targ,
                            "path": curpath,
                            "type": "file_system",
                            "_history": hittarg,
                          }
                paths[hittargindex] = elemdct
                config.save()
                print 'GO9_go_targets="$(go9.py gotargets export)"'
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
        """Edit all supported filetypes (currently hardcoded in this function).
            subcmds:
                [recurse] - then recurse subdirectories
        """
        dct = self.cmddict
        from glob import glob
        Ajss = []
        Ahtmls = []
        Apys = []
        Ashs = []
        Acsss = []
        Acpp  = []
        spccmds=self.config.get("spc_cmds");
        info( "go9py214: %s" % spccmds)
        ne = None
        if spccmds != None:
            nedict = spccmds["new_editor"] if "new_editor" in spccmds else None
            if isinstance(nedict,basestring):
                # repair
                nedict = {"command": nedict}
                ne = nedict["command"]
                self.config.set("spc_cmds.new_editor", nedict)
            elif isinstance(nedict, dict):
                ne = nedict["command"]
        
        if ne == None:
            os.environ["EDITOR"] if "EDITOR" in os.environ else None
        #info( "go9py217: %s" % ne)
        if ne == None:
            info("No 'new_editor' element. Add spc_cmds.new_editor string:")
            info('    "new_editor": "gedit -n {files}"')
            return ""
        editor = ne
        
        for root, dirs, files in os.walk("."):
            Ajss  .extend(glob(os.path.join(root, "*.js"  )))
            Ahtmls.extend(glob(os.path.join(root, "*.html")))
            Apys  .extend(glob(os.path.join(root, "*.py"  )))
            Ashs  .extend(glob(os.path.join(root, "*.sh"  )))
            Acsss .extend(glob(os.path.join(root, "*.css" )))
            Acpp  .extend(glob(os.path.join(root, "*.c")))
            Acpp  .extend(glob(os.path.join(root, "*.h")))
            Acpp  .extend(glob(os.path.join(root, "*.hh")))
            Acpp  .extend(glob(os.path.join(root, "*.c")))
            Acpp  .extend(glob(os.path.join(root, "*.cc")))
            Acpp  .extend(glob(os.path.join(root, "*.cpp")))
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
            cpps = " ".join(Acpp)
            files = '{jss} {htmls} {pys} {shs} {cpps}'.format(
                        cpps=cpps, jss=jss, htmls=htmls, pys = pys, shs = shs)
            editline = ne.format(files=files)+ " &"
            print editline
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
        if len(keys) == 0:
            print "echo No 'go' commands yet saved, use 'go9 add <tag>' to save current directory."
            return 
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
    cmddict["rmturds"] = {"function": rmturds,
                            "help":"""
Used to remove editor droppings, 'rm *~'.
                                    """.strip()
                           }
    def run(self, cmd, targ):
        runcmds = self.run_cmds
        if targ in runcmds:
            print ("%s" % runcmds[targ]["command"])
        else:
            info("No such run command: %s" % targ)
    cmddict["run"] = {"function": run,
                       "help": """
go9 run <run_key>
    Used to execute a bash command. 
                                """.strip(), 
                        # subcmds filled in __init__
                       }
    def runcmds(self, cmd, targ):
        run_cmds = self.config.get("run_cmds", {})
        cmdstrs = run_cmds.keys()
        cmdstrs.sort()
        if self.config.cliargs.export:
            # handles the difference of sending a list to go9.sh for "export" commands
            # and "printing" which happens to stderr.
            print " ".join(cmdstrs)
        else:
            for cmdstr in cmdstrs:
                cmdx = run_cmds[cmdstr]
                if blessed:
                    cmdstr = TERM.on_red(cmdstr)
                    print "echo",cmdstr
                info ("command name: %s" % cmdstr)
                info ("\t%s" % cmdx["command"])
            
    ## put in command dictionary
    cmddict["runcmds"] = {  "function": runcmds,
                            "help": """
go9 runcmds
    Used to list the run_cmds.
                                    """.strip()
                          }
                          
    def saveruncmd(self, cmd, targ):
        run_cmd = self.config.cliargs.run_cmd
        if not run_cmd:
            if self.config.cliargs.positional:
                if len(self.config.cliargs.positional) > 0:
                    run_cmd = self.config.cliargs.positional[0]
                    if len(self.config.cliargs.positional) > 1:
                        error("These args not used:\n\t%s" % self.config.cliargs.positional[1:])
        run_cmds = self.config.get("run_cmds", {})
        cmdstrs = run_cmds.keys()
        if targ in cmdstrs:
            error("run cmd '%s' already exists" % targ)
            error("\t%s" % run_cmds[targ]["command"])
        elif not run_cmd:
            error("no command given")
        else:
            run_cmds[targ]={"command":run_cmd}
            self.config.set("run_cmds", run_cmds)
            self.config.save()

    ## save as command
    cmddict["saveruncmd"] = {"function": saveruncmd,
                            "help":"""
go9 saveruncmd <run_name> "<cmd>"
                                    """.strip()
                            }

    def savelast(self, cmd, targ):
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
        echo choosing " $_GO9_lastcmd";;
   n|N )
        echo "Ok nvm.";;
   "" ) echo "what?";;
   * ) 
        echo "other";;
esac
'''.format() )
                    
        print outbuff

    ## put in command dictionary
    cmddict["savelast"] = savelast
    
    def refresh_cmd(self, cmd,targ):
        print 'GO9_go_targets="$(go9.py gotargets export)"'
        self.do_cmd("exportdirs")
        # reload go9.sh which is in my own directory
        go9ScriptFilename = os.path.join(os.path.dirname(__file__), 'go9.sh')
        go9ScriptFile = open(go9ScriptFilename)
        go9Script = go9ScriptFile.read()
        print go9Script

    ## put in command dictionary
    cmddict["refresh"] = refresh_cmd
    
    # some commands want other commands as targets... for autocomplete
    cmddict["help"]["subcmds"] = cmddict.keys()
    cmddict["listsubcmds"]["subcmds"] = cmddict.keys()
    
    def spccmds(self, cmd, targ):
        spc_cmds = self.config.get("spc_cmds", {})
        cmdstrs = spc_cmds.keys()
        cmdstrs.sort()
        if self.config.cliargs.export:
            # handles the difference of sending a list to go9.sh for "export" commands
            # and "printing" which happens to stderr.
            print " ".join(cmdstrs)
        else:
            for cmdstr in cmdstrs:
                cmdx = spc_cmds[cmdstr]
                info ("command name: %s" % cmdstr)
                info ("\t%s" % cmdx["command"])
            
    ## put in command dictionary
    cmddict["spccmds"] = {  "function": spccmds,
                            "help": """
go9 spccmds
    Used to list the spc_cmds (special commands such as 'editor').
                                    """.strip()
                          }
# set up parser for command line options

class ArgumentParserError(Exception): pass

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

class HelpAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(HelpAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print 'echo %r %r %r' % (namespace, values, option_string)
        
parser = ThrowingArgumentParser(description="Helper for go9 environment.",
            add_help=False)
parser.add_argument("cmd", default=None, nargs = "?",
                    help="Path(s) to recurse for targets.")
parser.add_argument("target", default=None, nargs = "?",
                    help="The target of the command")
parser.add_argument("positional", nargs = "*", help="Extra positional args")
parser.add_argument("--run_cmd", type=str, default=None, help="For a bash command.")
parser.add_argument("-x", "--export", default=False, action="store_true",
                    help="triggers the 'export' mode for some commands"
                    )
parser.add_argument("--config", default=None, 
                    help="Config file to load")
parser.add_argument('-f', "--force", default=False, action="store_true")
parser.add_argument('-h', '--help', action= HelpAction)


try:
    args = parser.parse_args()
except:
    print "echo Unknown argumentation. Use \\'go9 help\\' for more information."
    sys.exit()

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
    info("Warning: NO CONFIG, creating one at ~/.config/go9.conf")
    configname = None

try:
    #  info("loading %s" % configname)
    config = Config(configname, cmdline_args = args)
    if configname == None:
        config.save("{home}/.config/go9.conf".format(home = os.environ["HOME"]) )
except:
    #Exception("Can't Load %s" % configname)
    err("Can't Load %s" % configname)
    raise


go9cmd = Go9Command(config);
        
go9cmd.do_cmd(cmd, targ)
