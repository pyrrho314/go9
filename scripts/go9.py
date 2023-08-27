#!/usr/bin/env python3

# go9.py  
# The role of this program is to generate executable bash script.
# The code is executed by the go9 bash environment functions
# placed in the environment when go9.sh is sourced in the users
# .bashrc
#

import os,sys
import json
import argparse
import types
from go9util import partlocator
from go9util.ksutil import dict2pretty, publicKeys

try:
    import blessed
    TERM=blessed.Terminal()
except:
    blessed = None
    TERM=None


#############                                                                 #
#
# Notice:
#
# * When this program "prints" something, it's sent to bash.
#   The output needs to be a valid bash command.
#     `print("ls -laF")`
#
# * To "print" stuff to be read, use `info(..)` or `error(..)`                
#                                                                             #
                                                                  #############


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
            elif isinstance(cfgdict, str):
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


        self.cmddict = {
        "add": {
            "function": self.add,
            "help": """
go9 add <dir_key> -f
    Used to add current directory
                        """.strip()
        },
        #####################################33
        "delete": {
            "function": self.delete,
            "help": """
go9 delete <dir_key>
    Used to delete a directory from the go table.
                        """.strip()
        },
        #####################################33
        "editall": {
            "function": self.editall,
            "subcmds": ["recurse"],
            "help": """
go9 editall [recurse]
    Used to edit all appropriate file types. If recurse present, go
    through sub-directories.  Currently the file types and editor
    is hardcoded. TODO: set edit command and extensions in .go9 config.
                                 """.strip()
        },
        #####################################33
        "exportdirs": {
            "function": self.exportdirs,
            "help":"""
go9 exportdirs
    Used to create bash environment variables for each go9
    directory. The vars are of the form GO9DIR_<dir_key>.
                                    """.strip()
        },
        #####################################33
        "help": {
            "function": self.help,
            "help": """
go9 help <go9_cmd>
    Used to get information about the commands in go9 tool.
                        """.strip()
        },
        #####################################33
        "go": {
            "function": self.go,
            "help": """
go9 go <dir_key>
go <dir_key>
    Used to change to a target directory. If <dir_key> is
    absent, all targets will be listed.
                            """.strip()
        },
        #####################################33
        "gotargets": self.gotargets,
        "list": self.list,
        "listcmds": self.listcmds,
        "listsubcmds": { "function": Go9Command.listsubcmds },
        "run": {
            "function": self.run,
            "help": """
go9 run <run_key>
    Used to execute a bash command.
                                    """.strip(),
            # subcmds filled in __init__
        },
        #####################################33
        "rmturds": {
            "function": self.rmturds,
            "help":"""
Used to remove editor droppings, 'rm *~'.
                                    """.strip()
        },
        #####################################33
        "listruncmds": {
            "function": self.listruncmds,
            "help": """
go9 listruncmds
    Used to list the run_cmds.
                                    """.strip()
        },
        #####################################33
        "saveruncmd": {
            "function": self.saveruncmd,
            "help":"""
go9 saveruncmd <run_name> "<cmd>"
                                    """.strip()
        },
        #####################################33
        "savelast": self.savelast,
        #####################################33
        "refresh": self.refresh_cmd,
        #####################################33
        # some commands want other commands as targets... for autocomplete
        "help": {
            "subcmds": self.cmddict.keys(),
            "function": self.help,
        },
        #####################################33
        "listsubcmds": {
            "subcmds": self.cmddict.keys(),
            "function": self.listsubcmds,
        },
        #####################################33
        "spccmds": {
            "function": self.spccmds,
            "help": """
go9 spccmds
    Used to list the spc_cmds (special commands such as 'editor').
                                    """.strip()
        },
        #####################################33
        "whereami": self.whereami,
        }

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

        cmdlist = list(self.cmddict.keys())
        if cmd in cmdlist:
            cmddef = self.cmddict[cmd]
            if not isinstance(cmddef, dict):
                cmddef = {"function": cmddef}
            
            #info(f"cmddef={json.dumps(list(cmddef['subcmds']))}")

            # cmddef["function"](self, cmd, targ)
            # info(f"cmd {cmd}")
            cmddef["function"](cmd, targ)
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
                print('GO9_go_targets="$(go9.py gotargets export)"')
            else:
                elemdct =   {
                            "go_name": targ,
                            "path": curpath,
                            "type": "file_system"
                            }
                paths.append(elemdct)
            # info(dict2pretty("gpy111: paths", paths))
                config.save()
                print('GO9_go_targets="$(go9.py gotargets export)"')
        else:
            err("No target name!")
    
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
        print('GO9_go_targets="$(go9.py gotargets export)"')

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
            if isinstance(nedict, str):
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
            print(editline)
        else:
            info ("no appropriate files found")
    
    def exportdirs(self, cmd, targ):
        dct = self.go9dict
        targs = dct.keys()
        for targx in targs:
            targx = targx.replace(".","_")
            print("export GO9DIR_{targ}={path};".format(targ=targx, path=dct[targx]["path"]))
    
    def help(self, cmd, targ):
        if targ in self.cmddict:
            cd = self.cmddict[targ]
            cdhaskeys = hasattr(cd, '__iter__')
            if cdhaskeys and ("help" in cd):
                info(cd["help"])
            else:
                info ("Sorry, no info on '%s'" % targ)
        else:
            info("go9 commands")
            cmds = list(self.cmddict.keys())
            cmds.sort()
            info("\t%s" % "\n\t".join(cmds))
    
    def go(self, cmd, targ):
        dct = self.go9dict
        if targ == None:
            self.do_cmd("list")
        elif targ in dct:
            print(f'cd "{dct[targ]["path"]}"')
        else:
            print(f'echo \"No go_name == {targ}\"')

    def gotargets(self, cmd, targ):
        dct = self.go9dict
        targs = list(dct.keys())
        targs.sort()
        if targ == "export":
            print(" ".join(targs))
        else:
            for targstr in targs:
                print(f"echo \"{targstr}\";\n")
    
    def list(self, cmd, targ):
        dct = self.go9dict
        keys = list(dct.keys())
        if len(keys) == 0:
            print("echo No 'go' commands yet saved, use 'go9 add <tag>' to save current directory.")
            return
        keys.sort()
        maxkeylen = len(max(keys, key= lambda p: len(p)))+1
        keyfrag = "{key: >%d}" % maxkeylen
        for key in keys:
            showline = True
            if targ:
                showline = targ in key
            if showline:
                formstr = f'echo "{key} ==> {dct[key]["path"]}";\n'
                print(formstr)
    
    def listcmds(self, cmd, targ):
        autocmds = self.cmddict.keys()
        cmds = []
        cmds.extend(autocmds)
        if targ == "export":
            print(" ".join(cmds))
        else:
            for cmdstr in cmds:
                print("echo \"%s\";\n" % cmdstr)

    def listsubcmds(self, cmd, targ):
        if targ in self.cmddict:
            subcmds = None
            cmdict = self.cmddict[targ]
            if isinstance(cmdict, dict):
                subcmds = cmdict["subcmds"] if "subcmds" in cmdict else None

            if self.config.cliargs.export:
                if subcmds and len(subcmds) > 0:
                    print(" ".join(subcmds))
            else:
                if subcmds and len(subcmds) > 0:
                    print('echo "{scmds}"'.format(scmds = " ".join(subcmds)))

    def rmturds(self, cmd, targ):
        from glob import glob
        junk = " ".join(glob("*~"))
        print(f'rm {junk}')
    
    def run(self, cmd, targ):
        runcmds = self.run_cmds
        if targ in runcmds:
            print("%s" % runcmds[targ]["command"])
        else:
            info("No such run command: %s" % targ)

    def listruncmds(self, cmd, targ):
        run_cmds = self.config.get("run_cmds", {})
        cmdstrs = list(run_cmds.keys())
        cmdstrs.sort()
        if self.config.cliargs.export:
            # handles the difference of sending a list to go9.sh for "export" commands
            # and "printing" which happens to stderr.
            print(" ".join(cmdstrs))
        else:
            for cmdstr in cmdstrs:
                cmdx = run_cmds[cmdstr]
                if blessed:
                    cmdstr = TERM.on_red(cmdstr)
                    print("echo",cmdstr)
                info ("command name: %s" % cmdstr)
                info ("\t%s" % cmdx["command"])

    
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

        print(outbuff)

    def refresh_cmd(self, cmd,targ):
        print('GO9_go_targets="$(go9.py gotargets export)"')
        self.do_cmd("exportdirs")
        # reload go9.sh which is in my own directory
        go9ScriptFilename = os.path.join(os.path.dirname(__file__), 'go9.sh')
        go9ScriptFile = open(go9ScriptFilename)
        go9Script = go9ScriptFile.read()
        print(go9Script)

    def spccmds(self, cmd, targ):
        spc_cmds = self.config.get("spc_cmds", {})
        cmdstrs = list(spc_cmds.keys())
        cmdstrs.sort()
        if self.config.cliargs.export:
            # handles the difference of sending a list to go9.sh for "export" commands
            # and "printing" which happens to stderr.
            print(" ".join(cmdstrs))
        else:
            for cmdstr in cmdstrs:
                cmdx = spc_cmds[cmdstr]
                info ("command name: %s" % cmdstr)
                info ("\t%s" % cmdx["command"])

    def whereami(self, cmd, targ):
        cwd = os.path.abspath(os.path.curdir)
        path2go = {}
        dct = self.go9dict
        keys = list(dct.keys())
        keys.sort()
        maxkeylen = len(max(keys, key= lambda p: len(p)))+1
        keyfrag = "{key: >%d}" % maxkeylen
        for key in keys:
            path = dct[key]["path"]
            pathparts = path.split("/")
            pathdot = ".".join(pathparts)
            partlocator.set_property(path2go, pathdot+"._target", key)
            partlocator.set_property(path2go, pathdot+"._fullpath", path)
            #showline = True
            #showline = path == cwd
            #if showline:
            #    formstr = 'echo "%s ==> {path}";\n' % keyfrag
            #    print(formstr.format(
            #                    key=key, path=dct[key]["path"]))
        cwdary = cwd.split("/");
        cwdkey = ".".join(cwdary);
        parentary = cwdary[0:-1];
        parentkey = ".".join(parentary);
        currentTarget = partlocator.get_property(path2go, cwdkey+"._target")
        parentDict = partlocator.get_property(path2go, parentkey );
        parentTarget = partlocator.get_property(path2go, parentkey+"._target" )
        # children and siblings (no recursion)
        currentDict = partlocator.get_property(path2go, cwdkey)
        childkeys = publicKeys(currentDict)
        siblingkeys = publicKeys(parentDict)

        def getChildKeyAndTarg(key):
            target = partlocator.get_property(path2go, cwdkey+"."+key+"._target")
            return "\({key}\) \\'{target}\\'".format(key=key, target=target)
        def getSiblingKeyAndTarg(key):
            
            target = partlocator.get_property(path2go, parentkey+"."+key+"._target")
            # don't report me as my own sibling
            if (target == cwdary[-1]):
                return "myself"
            return "\({key}\) \\'{target}\\'".format(key=key, target=target)


        childKeysAndTargs = map(getChildKeyAndTarg, childkeys)
        siblingKeysAndTargs = map(getSiblingKeyAndTarg, siblingkeys)
        siblingKeysAndTargs = filter(lambda x: x != "myself", siblingKeysAndTargs)
        if currentTarget:
            print("echo current directory \({cd}\) is called \\'{targ}\\'".format(targ=currentTarget,
                                                                            cd=cwdary[-1]))
        else:
            print("echo current directory \({cd}\) is not a go target".format(cd=cwdary[-1]))

        parentname = (parentDict["_target"]
                        if ("_target" in parentDict)
                        else "\<not named\>")
        print("echo '  parent': \({parentname}\) \\'{parenttarget}\\'".format(
            parentname=parentname, parenttarget=parentTarget))
        print("echo children: {children}".format(
                                        children=
                                            ", ".join(childKeysAndTargs)
                                            if childkeys and len(childkeys) > 0
                                            else "\<not named\>"))
        print("echo siblings: {siblings}".format(
                                        siblings=
                                            ", ".join(siblingKeysAndTargs)
                                            if siblingkeys and len(siblingkeys) > 0
                                            else "\<not named\>"))

        # info(dict2pretty("currentDict", currentDict))
        # info(dict2pretty("parentDict", publicKeys(parentDict)))

  
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
        print(f'echo {namespace!r} {values!r} {option_string!r}')

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
    print("echo Unknown argumentation. Use \\'go9 help\\' for more information.")
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
        home = os.environ["HOME"]
        configDir = os.path.join(home, ".config")
        newconfigname = os.path.join(configDir,"go9.conf")
        if not os.path.exists(configDir):
            os.makedirs(configDir)
        config.save(newconfigname)
except:
    #Exception("Can't Load %s" % configname)
    err("Can't Load %s" % configname)
    raise


go9cmd = Go9Command(config);

go9cmd.do_cmd(cmd, targ)
