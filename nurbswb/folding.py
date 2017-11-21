
# from say import *
# import nurbswb.pyob
#------------------------------
import FreeCAD,FreeCADGui,Sketcher,Part

App = FreeCAD
Gui = FreeCADGui

import numpy as np
import time


class FeaturePython:
	''' basic defs'''

	def __init__(self, obj):
		obj.Proxy = self
		self.Object = obj

	def attach(self, vobj):
		self.Object = vobj.Object

	def claimChildren(self):
		return self.Object.Group

	def __getstate__(self):
		return None

	def __setstate__(self, state):
		return None


class ViewProvider:
	''' basic defs '''

	def __init__(self, obj):
		obj.Proxy = self
		self.Object = obj

	def __getstate__(self):
		return None

	def __setstate__(self, state):
		return None

#-------------------------------


class Folding(FeaturePython):
	def __init__(self, obj,uc=5,vc=5):
		FeaturePython.__init__(self, obj)

		obj.addProperty("App::PropertyInteger","count","config", "count of segments").count=20
		obj.addProperty("App::PropertyInteger","maxi","config", "animation folding")
		obj.addProperty("App::PropertyLink","faceobj","config","face to envelope")
		obj.addProperty("App::PropertyInteger","facenumber","config", "number of the face")
		obj.addProperty("App::PropertyLink","trackobj","config","track for envelope")
		obj.addProperty("App::PropertyLink","arcobj","config","curvature for envelope")
		obj.addProperty("App::PropertyFloat","factor","config", "scale the curvature in percent").factor=100
		obj.addProperty("App::PropertyBool","useSplines","config", "use Spline instead of Polylines").useSplines=True



	def attach(self,vobj):
		self.Object = vobj.Object
		self.obj2 = vobj.Object

	def onChanged(self, fp, prop):
		if prop=="count" or prop=="maxi" or prop=="factor":
			try: fp.Shape=fold(fp)
			except: pass

	def execute(self, fp):
		fp.Shape=fold(fp)


def createFolding(obj=None):

	a=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Folding")
	Folding(a)
	ViewProvider(a.ViewObject)
	return a




def fold(obj):

	bs=obj.faceobj.Shape.Face1
	track=obj.trackobj.Shape
	cuarcs=obj.arcobj.Shape

	count=obj.count

	pats=cuarcs.discretize(count)
	arcs=[p.y for  p in pats]

	ptsa=[]
	ptsb=[]

	try: curve=track.Curve
	except: curve=track.Edges[0].Curve

	tps=track.discretize(count)
	for p in tps:
			v=curve.parameter(p)
			t=curve.tangent(v)
			n=t[0].cross(FreeCAD.Vector(0,0,1))
			polg=Part.makePolygon([p+10000*n,p-10000*n])
			ss=bs.makeParallelProjection(polg,FreeCAD.Vector(0,0,1))
			sps=[v.Point for v in ss.Vertexes]
			#print sps
			if len(sps) == 2:
				ptsa += [sps[0]]
				ptsb += [sps[1]]
			if len(sps) == 1:
				ptsa += [sps[0]]
				ptsb += [sps[0]]

	ppsa=[]
	ppsb=[]

	segments=App.ActiveDocument.getObject("Segments")
	if segments==None:
		segments=App.ActiveDocument.addObject("Part::Feature","Segments")

	comp=[]
	for i,p in enumerate(ptsa):
		if ptsa[i]<>ptsb[i]:
			pol=Part.makePolygon([ptsa[i],ptsb[i]])
			comp.append(pol)
	segments.Shape=Part.Compound(comp)


	for i,p in enumerate(ptsa):

		if i<obj.maxi or obj.maxi==0:

			if i==0:
				matrix3=FreeCAD.Placement(FreeCAD.Vector(0,0,0),
					FreeCAD.Rotation(ptsa[i]-ptsb[i],
					0.01*obj.factor*arcs[0]),ptsa[i]).toMatrix()
			else:
				matrix3=FreeCAD.Placement(FreeCAD.Vector(0,0,0),
					FreeCAD.Rotation(ptsa[i]-ptsb[i],
					0.01*obj.factor*(arcs[i]-arcs[i-1])),ptsa[i]).toMatrix()

		else:
			matrix3=FreeCAD.Placement().toMatrix()

		a=ptsa[i]
		b=ptsb[i]

		if i==len(ptsa)-1 or i==0: a,b=b,a

		ppsa2=[  matrix3.multiply(p) for p in ppsa] + [a]
		ppsa=ppsa2

		ppsb2=[  matrix3.multiply(p) for p in ppsb] + [b]
		ppsb=ppsb2

	if obj.useSplines:
		ca=Part.BSplineCurve()
		ca.interpolate(ppsa)
		cb=Part.BSplineCurve()
		cb.interpolate(ppsb)
		ll=Part.makeLoft([ca.toShape(),cb.toShape()])
	else:
		ll=Part.makeLoft([Part.makePolygon(ppsa),Part.makePolygon(ppsb)])
	return ll



def run():

	ss=Gui.Selection.getSelection()

	folder=createFolding(obj=None)
	folder.faceobj=ss[0]
	folder.trackobj=ss[1]
	folder.arcobj=ss[2]

	App.activeDocument().recompute()