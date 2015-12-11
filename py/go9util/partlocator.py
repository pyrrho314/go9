import re
from astrodata.adutils import ksutil
from astrodata.adutils import termcolor as tc

class BadAddr:
    msg = "Bad Address"
    def __init__(self, msg = "Bad Address Error"):
        self.msg = msg
    def __str__(self):
        return self.msg
    
class AddrPart():  
    key = None
    content = None
    struct = None
    scope = 0 # integer
    pl = None
    
    def __init__(self, key, struct = None):
        self.key = key
        self.struct = struct
        self.get_content()
    
    def _get_next_struct(self):
        content = self.get_content()
        # print "]gni]", self.__class__.__name__,self.key, self.index if hasattr(self, "index") else "-", self.struct
        return content
    next_struct = property(_get_next_struct)
    
    def get_content(self):
        return None
    
    def next_part(self):
        return self.pl.next_part(self)
        
    def set_content(self, val):
        self.struct[self.key] = val
    
    def terminal(self):
        isterm = (self.struct != None) and self.get_content() == None
        return isterm
    
    def __repr__(self):
        return str( (self.__class__.__name__, self.key, type(self.struct), type(self.next_struct)) )
    
class DictPart(AddrPart):
    def get_content(self):
        if self.struct:
            if self.key in self.struct:
                content = self.struct[self.key]
                return content
            else:
                return None
        else:
            return None
    def create_location(self):
        self.struct = {}
        return self.struct
        
class ListPart(AddrPart):
    def get_content(self):
        if self.struct:
            if self.key != None and self.key < len(self.struct):
                content = self.struct[self.key]
            else:
                content = None
            return content
        else:
            return None
        
    def create_location(self):
        if self.struct == None:
            self.struct = []
        for i in range( len(self.struct), self.key+1 ):
            self.struct.append(None)
        return self.struct
#class TerminalPart(AddrPart):
#    def get_content(self):
        

class PartLocator():
    struct = None
    pytype = None
    propaddr = None
    def __init__(self, partname, struct = {}, pytype = str):
        self.propaddr = partname
        self.struct = struct
        bits = partname.split(".")
        addr = bits[:-1]
        key  = bits[-1]
        self.parts = parts = []
        nbits = []
        self.pytype = pytype
        for bit in bits:
            m = re.match("(?P<key>.*?)\[(?P<index>[0-9])\]", bit)
            if m:
                nbits.append(m.group("key"))
                nbits.append("[%s]" % m.group("index"))
            else:
                nbits.append(bit)
        bits = nbits
        # handle lists
        #print "bits>",nbits
        
        self.struct = struct
        cstruct = struct
        for i in range(len(bits)):
            #print "cstruct",i,cstruct
            bit = bits[i]
            stype = type(cstruct)
            #print "stype]",stype
            m = re.match("\[(?P<index>[0-9])\]", bit)
            if cstruct == None:
                if m:
                    #create listpart
                    index = int(m.group("index"))
                    part = ListPart(index, cstruct )
                else:
                    #create dictpart
                    part = DictPart(bit, cstruct)
            elif type(cstruct) == dict:
                part = DictPart(bit, cstruct)
            elif type(cstruct) == list:
                if m:
                    index = int(m.group("index"))
                    part = ListPart(index, cstruct)
                else:
                    raise BadAddr("should be list index")
            else:
                raise BadAddr("val=%s type=%s ... should be <dict> or <list>" % (cstruct, type(cstruct)))
            
            cstruct = part.next_struct
            parts.append(part)
                
            
        #parts.append(TerminalPart(key, struct = cstruct))
        self.parts = parts
        for i in range(len(self.parts)):
            parts[i].scope = i
            parts[i].pl = self
    
    def create_location(self):
        clDBG = False
        done = False
        while (not done):
            latest=self.find_terminal()
            if latest:
                unmade = latest.next_part()
                if unmade:
                    a=unmade.create_location()
                    if clDBG:
                        print "pl152: UNMADE:",unmade
                    latest.set_content(a)
                    if clDBG:
                        print "pl154: clDBG:",latest
                else:
                    done = True
            else:
                done = True
        return self
                
    def get_reference(self):
        """this call returns a struct and key which can be used to get or set a value"""
        term = self.find_terminal()
        # print "pl160:", term
        if self.find_terminal():
            # supposed to return None if the location is accessible
            return (None, None)
        endpart = self.parts[-1]
        reftuple = (endpart.struct, endpart.key)
        return reftuple
    
    def find_terminal(self):
        for i in range(len(self.parts)):
            part = self.parts[i]
            if part.terminal() == False:
                continue
            if part.terminal() == None:
                return None # this should only happen PAST the terminal
            if part.terminal() == True:
                return part
        return None
    
    def terminal_string(pl):
        lines = []
        for i in range(len(pl.parts)):
            part = pl.parts[i]
            line = "".join([ksutil._pad_str( str(part.terminal()), 7), 
                            ksutil._pad_str( str(part.key), 10),
                            ksutil._pad_str( str(part.struct),20),
                            "key is %s"%type(part.key)
                            ])
            if part.terminal():
                line = tc.colored(line, color = None, on_color = "on_yellow", attrs=[])
                line += tc.colored(" ", color = None, on_color = None)
            lines.append(line)
        return "\n".join(lines)
        
    def property_value(self, val = None):
        if val == None:
            val = self.parts[-1].get_content()
            if self.pytype:
                try:
                    val = self.pytype(val)
                except:
                    # ok so we couldn't convert it
                    #print "pl207: can't %s to %s for %s" % (val, self.pytype, self.propaddr)
                    val = None
                    
                    
            return val
        else:
            # returning self to allow function chaing WHEN SETTING... @@REEVAL
            if self.pytype:
                val = self.pytype(val)
            self.parts[-1].set_content(val)
            return self
            
    def next_part(self, part):
        index = part.scope
        nindex = index+1
        if nindex >= len(self.parts):
            return None
        else:
            return self.parts[nindex]

    
def get_property(s, key, pytype = None):
    pl = PartLocator(key, s, pytype = None)
    return pl.property_value()

def set_property(s, key, val, pytype = None):
    pl = PartLocator(key, s, pytype = None)
    pl.create_location()
    pl.property_value(val)
    
