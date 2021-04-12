from __future__ import unicode_literals
from node import *
from jinja2 import Template
import re

import datetime


class tree(object):
    def __init__(self, root, logger=None, debug=False):
        self.read_ops = dict(list())
        self.readwrite_ops = str()
        self.write_ops = dict(list())
        self.action_ops = str()
        self.default_ops = str()
        self.debug=debug
        ##### package write selection
        self.vhdl = 1           # write vhdl types package
        self.vhdl_def = 1       # write vhdl defaults package
        self.yml2hdl = 2        # version of yml2hdl tool type yml output 0=disable yml output
        ##### setup logger
        self.log = logger
        if not self.log:
            self.log = logging.getLogger("main")
            formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            self.log.setLevel(logging.WARNING)
            uhal.setLogLevelTo(uhal.LogLevel.WARNING)
        ##### read the root node
        self.root = node(root,baseAddress=0,tree=self)

    ####
    # YML2HDL v1
    ####
    def generateYaml(self, baseName, current_node, members, description):
            with open(self.outFileName.replace("PKG.vhd","PKG.yml"),'a') as outFile:
                ##### Generate and print a VHDL record
                outFile.write("- " + baseName+":\n")
                maxNameLength = 25
                maxTypeLength = 12
                sorted_members = sorted(members.items(), key=lambda item: (current_node.getChild(item[0]).address<<32) + current_node.getChild(item[0]).mask)
                for memberName,member in sorted_members:
                    outFile.write("  - " + memberName + " : [ type: ")
                    member_type = re.sub("\(.*\\)", "", member.replace("std_logic_vector","logic").replace("std_logic","logic"))
                    outFile.write(member_type)
                    if ("downto" in member):
                        (high,low) = re.search(r'\((.*?)\)',member).group(1).replace("downto"," ").split()
                        length = int(high)-int(low)+1
                        outFile.write(", length: "+str(length))
                    # if len(description[memberName]) > 0:
                    #     outFile.write(", description: " + description[memberName])
                    outFile.write(" ]\n")
                if current_node.isArray():
                    array_index_string = "array: " + str(1 + max(current_node.entries.keys()))+", type: "
                    #array_index_string = "array: (" + str(min(current_node.entries.keys())) + " to " + str(max(current_node.entries.keys()))+"), type : "
                    outFile.write("\n- " + baseName + "_ARRAY: [" + array_index_string + baseName + "]")
                outFile.write("\n\n")
                outFile.close()
            return
    ####
    # YML2HDL v1
    ####
    ####
    # YML2HDL v2
    ####
    def generateYamlv2(self, baseName, current_node, members, description):
      with open(self.outFileName.replace("PKG.vhd","PKG.yml"),'a') as outFile:
        ##### Generate and print a VHDL record
        outFile.write("- " + baseName+":\n")
        maxNameLength = 25
        maxTypeLength = 12
        sorted_members = sorted(members.items(), key=lambda item: (current_node.getChild(item[0]).address<<32) + current_node.getChild(item[0]).mask)
        for memberName,member in sorted_members:
          outFile.write("  - " + memberName + " : [ type: ")
          member_type = re.sub("\(.*\\)", "", member.replace("std_logic_vector","logic").replace("std_logic","logic"))
          outFile.write(member_type)
          if ("downto" in member):
              (high,low) = re.search(r'\((.*?)\)',member).group(1).replace("downto"," ").split()
              length = int(high)-int(low)+1
              outFile.write(", length: "+str(length))
          # if len(description[memberName]) > 0:
          #     outFile.write(", description: " + description[memberName])
          outFile.write(" ]\n")
        if current_node.isArray():
            array_index_string = "array: " + str(1 + max(current_node.entries.keys()))+", type: "
            #array_index_string = "array: (" + str(min(current_node.entries.keys())) + " to " + str(max(current_node.entries.keys()))+"), type : "
            outFile.write("\n- " + baseName + "_ARRAY: [" + array_index_string + baseName + "]")
        outFile.write("\n\n")
        outFile.close()
        return
    ####
    # YML2HDL v2
    ####

    def generateRecord(self, baseName, current_node, members, description):
        with open(self.outFileName,'a') as outFile:
            ##### Generate and print a VHDL record
            outFile.write("  type " +baseName+ " is record\n")
            maxNameLength = 25
            maxTypeLength = 12
            sorted_members = sorted(members.items(), key=lambda item: (current_node.getChild(item[0]).address<<32) + current_node.getChild(item[0]).mask)
            for memberName,member in sorted_members:
                if len(memberName) > maxNameLength:
                    maxNameLength = len(memberName)
                if len(member) > maxTypeLength:
                    maxTypeLength = len(member)
                outFile.write("    " + memberName + "".ljust(maxNameLength-len(memberName),' ') + "  :")
                outFile.write((member+';').ljust(maxTypeLength+1,' '))
                if len(description[memberName]) > 0:
                    outFile.write("  -- " + description[memberName])
                outFile.write('\n')
            outFile.write("  end record " +baseName+ ";\n")
            if current_node.isArray():
                array_index_string = " is array(" + str(min(current_node.entries.keys())) + " to " + str(max(current_node.entries.keys()))+") of "
                outFile.write("  type " + baseName + "_ARRAY" + array_index_string + baseName + ";")
            outFile.write("\n\n")
            outFile.close()
        ##### TODO: return value here?
        return 

    def generateDefaultRecord(self, baseName, defaults,outFileName):
        with open(outFileName,'a') as outfile:
            outfile.write("  constant DEFAULT_" + baseName + " : " + baseName +" := (\n")
            padding_size = 27 + (2 * len(baseName))
            firstLine=True
            for keys,values in defaults.items():
                # if the value is in the format of 0x1, translate it into x'1'
                if '0x' in values:
                    values=values.replace('0x','')
                    if values == '1':
                        values = "'1'"
                    else:
                        values='x"'+values+'"'
                if firstLine:
                    firstLine=False
                else:
                    outfile.write(",\n")
                outfile.write(" ".ljust(padding_size,' ')+keys+" => "+values)
            outfile.write("\n ".ljust(padding_size,' ')+");\n")
            outfile.close()
        return "DEFAULT_"+baseName

    def traversePkg(self, current_node=None, padding='\t'):
        if not current_node:
            current_node = self.root
        #print(padding+current_node.id+': ['+str([i.id for i in current_node.children]))
        package_mon_entries = dict()
        package_ctrl_entries = dict()
        package_ctrl_entry_defaults = dict()
        package_description = dict()
        package_addr_order = dict()
        for child in current_node.children:
            if len(child.children) != 0:
                child_records = self.traversePkg(child, padding+'\t')
                package_description[child.id] = ""
                array_postfix = ["","_ARRAY"][child.isArray()]
                ##### make the records for package entries
                if 'mon' in child_records:
                    package_mon_entries[child.id] = child.getPath(expandArray=False).replace('.','_')+'_MON_t'+array_postfix
                if 'ctrl' in child_records:
                    package_ctrl_entries[child.id] = child.getPath(expandArray=False).replace('.','_') + '_CTRL_t'+array_postfix
                if 'ctrl_default' in child_records:
                    default_package_entries = "DEFAULT_"+child.getPath(expandArray=False).replace('.','_')+"_CTRL_t"
                    if child.isArray(): default_package_entries = "(others => "+default_package_entries+" )"
                    package_ctrl_entry_defaults[child.id] = default_package_entries
            else:
                bitCount = bin(child.mask)[2:].count('1')
                package_entries = ""
                #if child.isArray():
                #    package_entries = "array("+str(min(child.entries.keys())) + ' to ' + str(max(child.entries.keys())) + ') of '
                if bitCount == 1:
                    package_entries += "std_logic"
                else:
                    package_entries += "std_logic_vector(" + str(bitCount-1).rjust(2,str(' ')) + " downto 0)"
                
                package_description[child.id] = child.description
                bits = child.getBitRange()
                if child.permission == 'r':
                    package_mon_entries[child.id] = package_entries
                elif child.permission == 'rw':
                    package_ctrl_entries[child.id] = package_entries
                    ##### store data for default signal
                    if "default" in child.parameters:
                        intValue = int(child.parameters["default"],0)
                        if bits.find("downto") > 0:
                            if bitCount % 4 == 0:
                                package_ctrl_entry_defaults[child.id] = "x\"" + hex(intValue)[2:].zfill(bitCount/4) + "\""
                            else:
                                package_ctrl_entry_defaults[child.id] = "\"" + bin(intValue)[2:].zfill(bitCount) + "\""
                        else:
                            package_ctrl_entry_defaults[child.id] = "'"+str(intValue)+"'"
                    elif bits.find("downto") > 0:
                        package_ctrl_entry_defaults[child.id] = "(others => '0')"
                    else:
                        package_ctrl_entry_defaults[child.id] = "'0'"
                elif child.permission == 'w':
                    ##### store data for default signal
                    if "default" in child.parameters:
                        print("Action register with default value!\n")
                    elif bits.find("downto") > 0:
                        package_ctrl_entry_defaults[child.id] = "(others => '0')"
                    else:
                        package_ctrl_entry_defaults[child.id] = "'0'"
                    package_ctrl_entries[child.id] = package_entries
        ret = {}
        if package_mon_entries:
            baseName = current_node.getPath(expandArray=False).replace('.','_')+'_MON_t'
            #print(padding+baseName)
            if self.vhdl:
              ret['mon'] = self.generateRecord(baseName, current_node, package_mon_entries, package_description)
            ####
            # YML2HDL v1
            ####
            if self.yml2hdl == 1:
              self.generateYaml(baseName, current_node, package_mon_entries, package_description)
            ####
            # YML2HDL v1
            ####

            if self.yml2hdl == 2:
              self.generateYamlv2(baseName, current_node, package_mon_entries, package_description)

        if package_ctrl_entries:
            baseName = current_node.getPath(expandArray=False).replace('.','_')+'_CTRL_t'
            #print(padding+baseName)
            if self.vhdl:
              ret['ctrl'] = self.generateRecord(baseName, current_node, package_ctrl_entries, package_description)
            ####
            # YML2HDL v1
            ####
            if self.yml2hdl == 1:
              self.generateYaml(baseName, current_node, package_ctrl_entries, package_description)

            ####
            # YML2HDL v2
            ####
            if self.yml2hdl == 2:
              self.generateYamlv2(baseName, current_node, package_ctrl_entries, package_description)

            if self.vhdl:
              ret["ctrl_default"] = self.generateDefaultRecord(baseName, package_ctrl_entry_defaults,self.outFileName)
            if self.vhdl_def:
              ret["ctrl_default"] = self.generateDefaultRecord(baseName, package_ctrl_entry_defaults,self.outFileName.replace("PKG.vhd","PKG_DEF.vhd"))
        return ret

    def generatePkg(self, outFileName=None):
        self.read_ops = dict(list())
        self.readwrite_ops = str()
        self.write_ops = dict(list())
        self.action_ops = str()
        outFileBase = self.root.id
        self.outFileName = outFileName
        #### Writing vhdl full header
        if self.vhdl:
          if not self.outFileName:
              self.outFileName = outFileBase + "_PKG.vhd"
          print("generatePkg : " + str(self.outFileName))
          with open(self.outFileName, 'w') as outFile:
              outFile.write("--This file was auto-generated.\n")
              outFile.write("--Modifications might be lost.\n")
              outFile.write("-- Created : "+str(datetime.datetime.now())+".\n")
              outFile.write("library IEEE;\n")
              outFile.write("use IEEE.std_logic_1164.all;\n")
              outFile.write("\n")
              # L0MDT shared common for yml2hdl v2 needed for special functions
              outFile.write("library shared_lib;\n")
              outFile.write("use shared_lib.common_ieee.all;\n")
              outFile.write("\n\npackage "+outFileBase+"_CTRL is\n")
              outFile.close()

        #### Writing vhdl defaults header
        if self.vhdl_def:
          if not self.outFileName:
            self.outFileName = outFileBase + "_PKG.vhd"
          defFileName =  self.outFileName.replace("PKG.vhd","PKG_DEF.vhd")
          print("generatePkg : " + str(defFileName))
          with open(defFileName, 'w') as outFile:
              outFile.write("--This file was auto-generated.\n")
              outFile.write("--Modifications might be lost.\n")
              outFile.write("-- Created : "+str(datetime.datetime.now())+".\n")
              outFile.write("library IEEE;\n")
              outFile.write("use IEEE.std_logic_1164.all;\n")
              outFile.write("\n")
              outFile.write("library ctrl_lib;\n")
              outFile.write("use ctrl_lib."+ outFileBase + "_CTRL.all;\n")
              outFile.write("\n\npackage "+outFileBase+"_CTRL_DEF is\n")
              outFile.close()

        ####
        # YML2HDL v1
        #### Writing yml header
        if self.yml2hdl == 1:
          self.outFileName = outFileName
          if not self.outFileName:
              self.outFileName = outFileBase + "_PKG.vhd"
          with open(self.outFileName.replace("PKG.vhd","PKG.yml"), 'w') as outFile:
              outFile.write("# This file was auto-generated.\n")
              outFile.write("# Modifications might be lost.\n")
              outFile.write("# Created : "+str(datetime.datetime.now())+".\n")
              outFile.write("__config__:\n")
              outFile.write("    basic_convert_functions : off\n")
              outFile.write("    packages:\n")
              outFile.write("    shared_lib:\n")
              outFile.write("        - common_ieee_pkg\n")
              outFile.write("\n")
              outFile.write("HDL_Types:\n")
              outFile.write("\n")
              outFile.close()

        ####
        # YML2HDL v2
        #### Writing yml header
        if self.yml2hdl == 2:
          self.outFileName = outFileName
          if not self.outFileName:
              self.outFileName = outFileBase + "_PKG.vhd"
          with open(self.outFileName.replace("PKG.vhd","PKG.yml"), 'w') as outFile:
              outFile.write("# yml2hdl v2\n")
              outFile.write("# This file was auto-generated.\n")
              outFile.write("# Modifications might be lost.\n")
              outFile.write("# Created : "+str(datetime.datetime.now())+".\n")
              outFile.write("config:\n")
              outFile.write("  basic_convert_functions : off\n")
              outFile.write("  packages:\n")
              outFile.write("    - ieee: [std_logic_1164, numeric_std, math_real]\n")
              outFile.write("    - shared_lib: [common_ieee]\n")
              outFile.write("\n")
              outFile.write("hdl:\n")
              outFile.write("\n")
              outFile.close()

        records = self.traversePkg()
        #### Ending full vhdl package
        if self.vhdl:
          with open(self.outFileName, 'a') as outFile:
            print("Closing : " + str(self.outFileName))
            outFile.write("\n\nend package "+outFileBase+"_CTRL;")
            outFile.close()
        #### Ending default package
        if self.vhdl_def:
          outfilepath = self.outFileName.replace("PKG.vhd","PKG_DEF.vhd")
          with open(outfilepath, 'a') as outFile:
            print("Closing : " + str(outfilepath))
            outFile.write("\n\nend package "+outFileBase+"_CTRL_DEF;")
            outFile.close()
        return


    @staticmethod
    def sortByBit(line):
        assignmentPos = line.find("<=")
        if assignmentPos < 0:
            return assignmentPos
        numberStart = line[0:assignmentPos].rfind("(")+1
        numberEnd = line[numberStart:assignmentPos].find("downto");
        if numberEnd < 0:
            numberEnd = line[numberStart:assignmentPos].find(")");
        if numberEnd < 0:
            return 0
        numberEnd+=numberStart
        return int(line[numberStart:numberEnd])

    @staticmethod
    def generateAlignedCase(operations):
        output = io.StringIO()
        newAssignmentPos = 0
        newAssignmentLength = 0
        for addr in operations:
            #find the position of the "<=" in each line so we can align them
            #find the max length of assignment names so we can align to that as well
            for line in operations[addr].split('\n'):
                assignmentPos = line.find("<=")
                if assignmentPos > newAssignmentPos:
                    newAssignmentPos = assignmentPos;            
                assignmentLength = line[assignmentPos:].find(";")
                if assignmentLength > newAssignmentLength:
                    newAssignmentLength = assignmentLength;            
        for addr in operations:
            output.write("        when "+str(addr)+" => --"+hex(addr)+"\n");
            for line in sorted(operations[addr].split('\n'),key = tree.sortByBit):                
                if line.find("<=") > 0:
                    preAssignment = line[0:line.find("<=")-1]
                    line=line[line.find("<=")+2:]
                    assignment = line[0:line.find(";")]
                    line=line[line.find(";")+1:]
                    output.write("          "+
                             preAssignment.ljust(newAssignmentPos)+
                             " <= "+
                             str(assignment+";").ljust(newAssignmentLength)+
                             "    "+
                             line+
                             "\n")
        return output.getvalue()

    def generate_r_ops_output(self):
        return self.generateAlignedCase(self.read_ops)

    def generate_w_ops_output(self):
        return self.generateAlignedCase(self.write_ops)

    def generate_rw_ops_output(self):
        output = io.StringIO()
        newAssignmentPos = 0
        newAssignmentLength = 0
        for line in self.readwrite_ops.split("\n"):
            assignmentPos = line.find("<=")
            if assignmentPos > newAssignmentPos:
                newAssignmentPos = assignmentPos;            
            assignmentLength = line[assignmentPos:].find(";")
            if assignmentLength > newAssignmentLength:
                newAssignmentLength = assignmentLength
        for line in self.readwrite_ops.split("\n"):
            if line.find("<=") > 0:
                preAssignment = line[0:line.find("<=")-1]
                line=line[line.find("<=")+2:]
                assignment = line[0:line.find(";")]
                line=line[line.find(";")+1:]
                output.write("  "+
                              preAssignment.ljust(newAssignmentPos)+
                              " <= "+
                              str(assignment+";").ljust(newAssignmentLength)+
                              "    "+
                              line+
                              "\n")
        return output.getvalue()

    def generate_a_ops_output(self):
        output = io.StringIO()
        for line in self.action_ops.split("\n"):
            output.write("      "+line+"\n")
        return output.getvalue()

    def generate_def_ops_output(self):
        output = io.StringIO()
        for line in self.default_ops.split("\n"):
            if(len(line)):
                output.write("      "+line.split("<")[0])
                output.write(" <= DEFAULT_"+self.root.id+"_"+line.split("=")[1].strip())
                output.write("\n")
        return output.getvalue()

    def traverseRegMap(self, current_node=None, padding='\t'):
      if not current_node:
        current_node = self.root
      ##### expand the array entries
      expanded_child_list = []
      for child in current_node.children:
        if child.isArray():
          for entry in child.entries.values():
            expanded_child_list.append(entry)
        else:
          expanded_child_list.append(child)
      ##### loop over expanded list
      for child in expanded_child_list:
        if len(child.children) != 0:
          self.traverseRegMap(child, padding+'\t')
        else:
          bits = child.getBitRange()
          if child.permission == 'r':
            read_op = "localRdData(%s) <= Mon.%s; -- %s\n" % (bits,child.getPath(includeRoot=False, expandArray=True),child.description)
            if child.getLocalAddress() in self.read_ops:
              self.read_ops[child.getLocalAddress()] += read_op
            else:
              self.read_ops[child.getLocalAddress()] = read_op
          elif child.permission == 'rw':
            # read
            read_op = "localRdData(%s) <= reg_data(%d)(%s); -- %s\n" % (bits, child.getLocalAddress(), bits, child.description)
            if child.getLocalAddress()  in self.read_ops:
              self.read_ops[child.getLocalAddress()] += read_op
            else:
              self.read_ops[child.getLocalAddress()] = read_op

            # write
            wr_op = "reg_data(%d)(%s) <= localWrData(%s); -- %s\n" % (child.getLocalAddress(),bits, bits,child.description)
            if child.getLocalAddress() in self.write_ops:
              self.write_ops[child.getLocalAddress()] += wr_op
            else:
              self.write_ops[child.getLocalAddress()] = wr_op

            # read/write
            self.readwrite_ops += "Ctrl.%s <= reg_data(%d)(%s);\n" % (child.getPath(includeRoot=False, expandArray=True),child.getLocalAddress(),bits)

            # default
            self.default_ops += "reg_data(%d)(%s) <= CTRL_t.%s;\n" % (child.getLocalAddress(),bits,child.getPath(includeRoot=False, expandArray=True))

          elif child.permission == 'w':

            # action_registers
            wr_ops_str = "Ctrl.%s <= localWrData(%s);\n" % (child.getPath(includeRoot=False, expandArray=True), bits)
            if child.getLocalAddress() in self.write_ops:
              self.write_ops[child.getLocalAddress()] += wr_ops_str
            else:
              self.write_ops[child.getLocalAddress()] = wr_ops_str

            # determine if this is a vector or a single entry
            others = "(others => '0')" if bits.find("downto") > 0 else "'0'"
            self.action_ops += "Ctrl.%s <= %s;\n" % (child.getPath(includeRoot=False, expandArray=True),others)

            # bits = child.getBitRange()
            # if child.permission == 'r':
            #     if child.getLocalAddress() in self.read_ops:
            #         self.read_ops[child.getLocalAddress()] = self.read_ops[child.getLocalAddress()] + str("localRdData("+bits+")")+" <= Mon."+child.getPath(includeRoot=False,expandArray=True)+"; --"+child.description+"\n"
            #     else:
            #         self.read_ops[child.getLocalAddress()] = str("localRdData("+bits+")")+" <= Mon."+child.getPath(includeRoot=False,expandArray=True)+"; --"+child.description+"\n"
            # elif child.permission == 'rw':
            #     if child.getLocalAddress()  in self.read_ops:
            #         self.read_ops[child.getLocalAddress()] = self.read_ops[child.getLocalAddress()] + str("localRdData("+bits+")")+" <= "+"reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+"); --"+child.description+"\n"
            #     else:
            #         self.read_ops[child.getLocalAddress()] = str("localRdData("+bits+")")+" <= "+"reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+"); --"+child.description+"\n"
            #     if child.getLocalAddress() in self.write_ops:
            #         self.write_ops[child.getLocalAddress()] = self.write_ops[child.getLocalAddress()] + str("reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+")") + " <= localWrData("+bits+"); --"+child.description+"\n"
            #     else:
            #         self.write_ops[child.getLocalAddress()] = str("reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+")") + " <= localWrData("+bits+"); --"+child.description+"\n"
            #     self.readwrite_ops+=("Ctrl."+child.getPath(includeRoot=False,expandArray=True)) + " <= reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+");\n"
            #     self.default_ops+="reg_data("+str(child.getLocalAddress()).rjust(2)+")("+bits+") <= "+("CTRL_t."+child.getPath(includeRoot=False,expandArray=True))+";\n"
            # elif child.permission == 'w':
            #     if child.getLocalAddress() in self.write_ops:
            #         self.write_ops[child.getLocalAddress()] = self.write_ops[child.getLocalAddress()] + ("Ctrl."+child.getPath(includeRoot=False,expandArray=True)) + " <= localWrData("+bits+");\n"
            #     else:                                                     
            #         self.write_ops[child.getLocalAddress()] = ("Ctrl."+child.getPath(includeRoot=False,expandArray=True)) + " <= localWrData("+bits+");\n"
            #     #determin if this is a vector or a single entry
            #     if bits.find("downto") > 0:
            #         self.action_ops+="Ctrl." + child.getPath(includeRoot=False,expandArray=True) + " <= (others => '0');\n"
            #     else:
            #         self.action_ops+="Ctrl." + child.getPath(includeRoot=False,expandArray=True) + " <= '0';\n"
      return

    def generateRegMap(self, outFileName=None, regMapTemplate="template_map.vhd"):
        outFileBase = self.root.id
        if not outFileName:
            outFileName = outFileBase+"_map.vhd"
        print("generateRegMap : " + str(outFileName))
        ##### traverse through the tree and fill the ops
        self.traverseRegMap()
        ##### calculate regMapSize and regAddrRange
        regMapSize=0
        if len(self.read_ops) and max(self.read_ops,key=int) > regMapSize:
            regMapSize = max(self.read_ops,key=int)
        if len(self.write_ops) and max(self.write_ops,key=int) > regMapSize:
            regMapSize = max(self.write_ops,key=int)
        if regMapSize>0:
            regAddrRange=str(int(math.floor(math.log(regMapSize,2))))
        else:
            regAddrRange='0'
        ##### read the template from template file
        with open(os.path.join(sys.path[0],regMapTemplate)) as template_input_file:
            RegMapOutput = template_input_file.read()
            RegMapOutput = Template(RegMapOutput)
            template_input_file.close()
        ##### Substitute keywords in the template
        substitute_mapping = {
            "baseName"      : outFileBase,
            "regMapSize"    : regMapSize,
            "regAddrRange"  : regAddrRange,
            "r_ops_output"  : self.generate_r_ops_output(),
            "rw_ops_output" : self.generate_rw_ops_output(),
            "a_ops_output"  : self.generate_a_ops_output(),
            "w_ops_output"  : self.generate_w_ops_output(),
            "def_ops_output": self.generate_def_ops_output(),
        }
        RegMapOutput = RegMapOutput.render(substitute_mapping)
        ##### output to file
        with open(outFileName,'w') as outFile:
            outFile.write(RegMapOutput)
            outFile.close()
        return
