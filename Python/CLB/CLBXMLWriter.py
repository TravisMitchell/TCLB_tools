# -*- coding: utf-8 -*-

import lxml.etree as ET

## DECORATORS ##

def geometryElement(func):
    def fin(self, *args, **kwargs):
        nargs = func(self, *args, **kwargs)

        if len(nargs) < 1 or \
        not nargs.has_key('_xml_node_name') \
        :
            raise BaseException("NOT ENOUGHT ARGS FOR GEOM ELEMENT")

        n = ET.SubElement(self.current_geometry,nargs['_xml_node_name'])
        for k in nargs:
            if not k == '_xml_node_name':
                n.set(k, str(kwargs[k]))
        return n
    return fin


def addCDATA(name):
    def nif(func):
        def fin(self, *args, **kwargs):
            n = func(self, *args, **kwargs)
            n.text = ET.CDATA(kwargs['eval'])
            #n.append(cdata)
        return fin
    return nif


def BCElement(func):
    def fin(self, *args, **kwargs):
        nargs = func(self, *args, **kwargs)

        if len(nargs) < 1 or \
        not nargs.has_key('_xml_node_name') \
        :
            raise BaseException("NOT ENOUGHT ARGS FOR BC ELEMENT")

        n = ET.SubElement(self.geometry,nargs['_xml_node_name'])
        for k in nargs:
            if not k == '_xml_node_name':
                n.set(k, str(kwargs[k]))

        self.current_geometry = n
        return self.current_geometry
    return fin


def defaultArg(name, value):
    def nif(func):
        def fin(self, *args, **kwargs):
            if not kwargs.has_key(name):
                kwargs[name] = value
            return func(self, *args, **kwargs)
        return fin
    return nif

def requireArg(name):
    def nif(func):
        def fin(self, *args, **kwargs):
            if not kwargs.has_key(name):
                raise BaseException("Argument "+str(name)+ " is required")
            return func(self, *args, **kwargs)
        return fin
    return nif



def addSimpleGeomElements(nameList):
    def nif(cls):
        def inf(name):
            @geometryElement
            def fin(self, **kwargs):
                kwargs['_xml_node_name'] = name
                return kwargs
            cls.__dict__["add"+name] = fin
        for n in nameList:
            inf(n)
        return cls
    return nif

def addSimpleBCElements(nameList):
    def nif(cls):
        def inf(name):
            @BCElement
            def fin(self, **kwargs):
                kwargs['_xml_node_name'] = name
                return kwargs
            cls.__dict__["add"+name] = fin
        for n in nameList:
            inf(n)
        return cls
    return nif


    
def _set_by_kw(kw, name, default):
    if kw.has_key(name):
        return kw[name]
    else:
        return default
        
        
@addSimpleGeomElements([
    'Box',
    'Sphere',
    'HalfSphere',
    'OffgridSphere',
    'OffgridPipe',
    'Outlet',
    'Inlet'
    ])
@addSimpleBCElements([
    'MRT',
    'ESymmetry',
    'NSymmetry',
    'MovingWall',
    'SSymmetry',
    'None',
    'EPressure',
    'WPressure',
    ])
       
class CLBConfigWriter:

    def __init__(self, sign=''):
        self.root = ET.Element('CLBConfig')
        if not sign == '':
            self.root.append(ET.Comment(sign))
        self.root.append(ET.Comment("Created using CLBConfigWriter"))

        self.geometry = ET.SubElement(self.root,'Geometry')
        self.model = ET.SubElement(self.root, 'Model')

        self.root.set("version", "2.0")
        self.root.set("output", "output/")
        self.geometry.set("predef", "none")
        self.geometry.set("model", "MRT")

        self.current_geometry = self.geometry


    def dump(self):
        self.indent(self.root)
        return ET.tostring(self.root)

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def write(self, filename):
        tree = ET.ElementTree(element=self.root) 
        tree.write(filename)

    def addModelParam(self, name, value):
        n = ET.SubElement(self.model,'Params')
        n.set(str(name), str(value))

    def addGeomParam(self, name, value):
        self.geometry.set(str(name), str(value))

    def setCG(self, cg):
        self.current_geometry = cg

    def addInit(self):
        ET.SubElement(self.root, 'Init')

    def addSave(self,iterations, fname):
        n = ET.SubElement(self.root, 'SaveBinary')
        n.set('Iterations', str(iterations))
        n.set('filename', str(fname))

    def addSolve(self, **kwargs):
        
        iterations = _set_by_kw(kwargs, 'iterations', 1)
        vtk = _set_by_kw(kwargs, 'vtk', 0)
        log = _set_by_kw(kwargs, 'log', 0)
        failcheck = _set_by_kw(kwargs, 'failcheck', 0)

        failcheck_nx = _set_by_kw(kwargs, 'failcheck_nx', 1)
        failcheck_ny = _set_by_kw(kwargs, 'failcheck_ny', 1)
        failcheck_nz = _set_by_kw(kwargs, 'failcheck_nz', 1)

        
        self.model = self.root
        n = ET.SubElement(self.root, 'Solve')
        n.set('Iterations', str(iterations))
        if vtk > 0:
            n2 = ET.SubElement(n, 'VTK')
            n2.set('Iterations', str(vtk))

        if log > 0:
            n3 = ET.SubElement(n, 'Log')
            n3.set('Iterations', str(log))
        if failcheck > 0:
            n3 = ET.SubElement(n, 'Failcheck')
            n3.set('Iterations', str(failcheck))
            n3.set('nx', str(failcheck_nx))
            n3.set('ny', str(failcheck_ny))
            n3.set('nz', str(failcheck_nz))
            ET.SubElement(n3, 'VTK')                
##############
# ELEMENT METHODE
#############
    @requireArg('name')
    @BCElement
    def addZoneBlock(self, **kwargs):
        kwargs['_xml_node_name'] = 'None'
        return kwargs

    @defaultArg('mask','ALL')
    @BCElement
    def addWall(self, **kwargs):
        kwargs['_xml_node_name'] = 'Wall'
        return kwargs

    @requireArg('file')
    @geometryElement
    def addText(self, **kwargs):
        kwargs['_xml_node_name'] = 'Text'
        return kwargs

    @requireArg('eval')
    @addCDATA('eval')
    @geometryElement
    def addPythonInline(self, **kwargs):
        kwargs['_xml_node_name'] = 'PythonInline'
        del kwargs['eval']
        return kwargs
##############
#  END ELEMENT FUNCTIONS, END CLASS
#############


if __name__ == "__main__":
    CLBc = CLBConfigWriter()
    CLBc.addGeomParam('ny', 256)
    CLBc.addGeomParam('nx', 160)
    
    
    CLBc.addMRT()
    CLBc.addBox()
    
    CLBc.addZoneBlock(name='zwet')
    
    CLBc.addBox(dy=90, fy=-90)
    
    CLBc.addWall(name="zwall")
    #CLBc.addSphere(dy=">128", ny="256", dx=">-128", nx="256")
    CLBc.addSphere(dy="0", ny="256", dx=">-128", nx="256")
    CLBc.addBox(fy=-1, nx=50)
    
    CLBc.addRightSymmetry()
    CLBc.addBox(fy=-1, dx=-1)
  
    CLBc.addPythonInline(nx=50, eval=""" 
def test(*args, **kwargs):    
    pass
    """)
  
    CLBc.addTopSymmetry()
    CLBc.addBox(fx=-1, dy=-1)
    
    params = {
    'InletVelocity': "0.0",
    'Density':"0.05",
    'Density-zwet':"3.117355002492964819",
    'Density-zwall':"2",
    'Density-zbc':"3.2625",
    'Temperature':"0.56",
    'FAcc':"1",
    'Magic':"0.008",
    'MagicA':"-0.152",
    'MagicF':"-0.6666666666666",
    'GravitationY':"-0.00000",
    'GravitationX':"-0.00000",
    'MovingWallVelocity':"0.000",
    'S0':"0",
    'S1':"0",
    'S2':"0",
    'S3':"-0.333333",
    'S4':"0",
    'S5':"0",
    'S6':"0",
    'S7':"0.00",
    'S8':"0.00"
    }
    
    for n in params:
        CLBc.addModelParam(n, params[n])
    
    CLBc.addSolve(iterations=1, vtk=1)
    CLBc.addSolve(iterations=100, vtk=50)
    
    CLBc.dump()
   # CLBc.write('/home/michal/tach-17/mnt/fhgfs/users/mdzikowski/yang-laplace-sphere-matrix/test.xml')
   