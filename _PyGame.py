import sys
sys.path.insert(0,'..')
import PythonOgreConfig

import random, math,pygame
from pygame.locals import *
import ogre.renderer.OGRE as ogre
import ode
import time
import ogre.gui.CEGUI as CEGUI
from ctypes import *

WINSIZE = [800, 600]
WINCENTER = [WINSIZE[0]/2, WINSIZE[1]/2]
NUMSTARS = 150
white = 255, 240, 200
black = 20, 20, 40

class PyGameOGREApp():
    "Provides a base for an application using PyGame and PyOgre"
    def __init__(self, width=WINSIZE[0], height=WINSIZE[1], fullscreen=False):
        self._initPyGame()
        self._initPyOgre()
        self._createWindow(width, height, fullscreen)
        self._createViewport()
        self._loadResources("resources.cfg")
        self._createEntities()
  
    def _initPyGame(self):
        "Starts up PyGame"
        pygame.init()
  
    def _initPyOgre(self):
        "Instantiates the PyOgre root and sceneManager objects and initialises"
        self.root = ogre.Root("plugins.cfg")
        self.root.showConfigDialog()
        self.root.initialise(False)
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "Default SceneManager")
  
    def _createWindow(self, width, height, fullscreen):
        "Creates a PyGame window and sets PyOgre to render onto it"
        #self.screen = pygame.display.set_mode((width,height), pygame.DOUBLEBUF|pygame.HWSURFACE|pygame.FULLSCREEN )
        self.screen = pygame.display.set_mode((width,height), pygame.RESIZABLE )
        renderParameters = ogre.NameValuePairList()
        renderParameters['externalWindowHandle'] = str(pygame.display.get_wm_info()['window'])
        self.renderWindow = self.root.createRenderWindow('PyOgre through PyGame', width, height, fullscreen, renderParameters)
        self.renderWindow.active = True

        #CEGUI Setup
        self.GUIRenderer = CEGUI.OgreRenderer.bootstrapSystem(self.renderWindow)
        self.GUIsystem = CEGUI.System.getSingleton()
  
    def _createViewport(self):
        "Creates the user's viewport and camera"
        self.camera = self.sceneManager.createCamera("camera")
        self.camera.position = (20, 200, 50)
        #self.camera.lookAt((2000, 80, -2000))
        self.camera.nearClipDistance = 5
        self.viewport = self.renderWindow.addViewport(self.camera)
        self.viewport.backgroundColour = (0, 0, 139)
  
    def _loadResources(self, rcfile):
        "Loads the resource paths from specified resource config file"
        cf = ogre.ConfigFile()
        cf.load("resources.cfg")
  
        seci = cf.getSectionIterator()
        while seci.hasMoreElements():
            secName = seci.peekNextKey()
            settings = seci.getNext()
  
            for item in settings:
                typeName = item.key
                archName = item.value
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(archName, typeName, secName)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()
  
  
    def _createEntities(self):
        "For simple demo purposes this can be used to create entities and attach them to sceneNode's"
        #self.entities = [self.sceneManager.createEntity("city", "city.mesh")]
        #self.entities[len(self.entities)-1].setMaterialName('Examples/RustySteel')
        #self.sceneNodes = [self.sceneManager.getRootSceneNode().createChildSceneNode("cityNode")]
        plane = ogre.Plane()
        plane.normal = ogre.Vector3().UNIT_Y
        plane.d = 100
        ogre.MeshManager.getSingleton().createPlane("Myplane",
            ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME, plane,
            1500,1500,20,20,True,1,60,60,ogre.Vector3().UNIT_Z)
        self.entities = [self.sceneManager.createEntity( "plane", "Myplane" )]
        #self.entities[len(self.entities)-1].setMaterialName("Examples/Rockwall")
        self.sceneNodes = [self.sceneManager.getRootSceneNode().createChildSceneNode("planeNode")]
        self.sceneNodes[len(self.sceneNodes)-1].setPosition(self.sceneNodes[len(self.sceneNodes)-1].getPosition() + (0, 100, 0))

##        self.testEnt = self.sceneManager.createEntity("test", "Sphere.mesh")
##        self.testNode = self.sceneManager.getRootSceneNode().createChildSceneNode("testNode")
##        self.testNode.attachObject(self.testEnt)
        
        self.cubeCount = 0
        self.sphereCount = 0
        for i in range(len(self.sceneNodes)):
            self.entities[i].setCastShadows(True)
            self.sceneNodes[i].attachObject(self.entities[i])
            self.sceneNodes[i].showBoundingBox(True)
        random.seed()
        self.clock = pygame.time.Clock()

        #Let's do some physics :D
        self.world = ode.World()
        self.world.setGravity((0,-0.9,0))
        
        #Create a space object
        self.space = ode.Space()
        
        #Create a Floor Plane
        self.floor = ode.GeomPlane(self.space, (0,1,0), 0)
        self.floor.name = "plane"

        #Some Physixs Holders
        self.bodies = []
        self.geoms = [self.floor]
        self.contactgroup = ode.JointGroup()
        
        #Create Body Object for camera
        self.cameraBody = ode.Body(self.world)
        M = ode.Mass()
        M.setSphere(70, 200)
        self.cameraBody.setMass(M)
        geom = ode.GeomSphere(self.space, 200)
        geom.setBody(self.cameraBody)
        #self.bodies.append(self.cameraBody)
        self.geoms.append(geom)

        #Some simulation variables
        self.cameraBody.setPosition(self.camera.getPosition())
        self.fps = 50
        self.dt = 1.0/self.fps
        self.state = 0
        self.counter = 0
        objcount = 0
        self.lasttime = time.time()

        #Sexy Shadows
        self.sceneManager.setShadowTechnique(ogre.SHADOWTYPE_STENCIL_ADDITIVE)
        #self.sceneManager.setShadowTechnique(ogre.SHADOWTYPE_TEXTURE_MODULATIVE)
        if self.root.getRenderSystem().getCapabilities().hasCapability(ogre.RSC_HWRENDER_TO_TEXTURE):
            ## In D3D, use a 1024x1024 shadow texture
            self.sceneManager.setShadowTextureSettings(1024, 2)
        else:
            ## Use 512x512 texture in GL since we can't go higher than the window res
            self.sceneManager.setShadowTextureSettings(512, 2)
        self.sceneManager.setShadowColour(ogre.ColourValue(0.6, 0.6, 0.6))

        #Draw crosshairs
        #Size of Screen: [800, 600]
        #CEGUI
##        CEGUI.SchemeManager.getSingleton().create("TaharezLook.scheme")
##        myImageWindow = CEGUI.WindowManager.getSingleton().createWindow("TaharezLook/StaticImage","MainWindow")
##        myImageWindow.setPosition(CEGUI.UVector2(CEGUI.UDim(1,0), CEGUI.UDim(1,0)))
##        myImageWindow.setSize(CEGUI.UVector2(CEGUI.UDim(0,800),CEGUI.UDim(0,600)))
##        myImageWindow.setProperty("Image","set:TaharezLook image:Crosshairs")
##        CEGUI.System.getSingleton().setGUISheet(myImageWindow)
##        myImageWindow3 = CEGUI.WindowManager.getSingleton().createWindow("TaharezLook/StaticImage","PrettyWindow")
##        myImageWindow3.setPosition(CEGUI.UVector2(CEGUI.UDim(0.5,-3.5), CEGUI.UDim(0.5,-10)))
##        myImageWindow3.setSize(CEGUI.UVector2(CEGUI.UDim(0,7),CEGUI.UDim(0,20)))
##        myImageWindow3.setProperty("Image","set:TaharezLook image:Crosshairs")
##        CEGUI.System.getSingleton().getGUISheet().addChildWindow(myImageWindow3)
##        myImageWindow2 = CEGUI.WindowManager.getSingleton().createWindow("TaharezLook/StaticImage","PrettyWindow2")
##        myImageWindow2.setPosition(CEGUI.UVector2(CEGUI.UDim(0.5,-10), CEGUI.UDim(0.5,-3.5)))
##        myImageWindow2.setSize(CEGUI.UVector2(CEGUI.UDim(0,20),CEGUI.UDim(0,7)))
##        myImageWindow2.setProperty("Image","set:TaharezLook image:Crosshairs")
##        CEGUI.System.getSingleton().getGUISheet().addChildWindow(myImageWindow2)
        
        #gui = CEGUI.System.getSingleton().getGUISheet()
        #gui.addChildWindow(myImageWindow)
        
    def near_callback(self, args, geom1, geom2):
##        try:
##            if geom1.getBody().name == "ray":
##                print geom2.name
##                self.rayOn = False
##                num = -1
##                for i in self.geoms:
##                    if i.name == geom2.name:
##                        num = i
##                if not num == -1:
##                    print "You Win :D"
##                    self.selected = self.sceneNodes[num+1]
##                    self.selection = True
##                    self.selectedEnt = self.entities[num+1]
##                    if str(geom2)[9] == 'B':
##                        self.selectedShape = "cube"
##                    elif str(geom2)[9] == 'S':
##                        self.selectedShape = "sphere"
##                else:
##                    print "You Fail :("
##                geom1.getBody().disable()
##                geom1.disable()
##                #self.geoms.remove(geom1)
##                return
##        except:
##            try:
##                if geom2.getBody().name == "ray":
##                    print geom1.name
##                    self.rayOn = False
##                    num = -1
##                    for i in self.geoms:
##                        if i.name == geom2.name:
##                            num = i
##                    if not num == -1:
##                        print "You Win :D"
##                        self.selected = self.sceneNodes[num+1]
##                        self.selection = True
##                        self.selectedEnt = self.entities[num+1]
##                        if str(geom1)[9] == 'B':
##                            self.selectedShape = "cube"
##                        elif str(geom1)[9] == 'S':
##                            self.selectedShape = "sphere"
##                    else:
##                        print "You Fail :("
##                    geom2.getBody().disable()
##                    geom2.disable()
##                    #self.geoms.remove(geom2)
##                    return
##            except:
##                st = "blah"
        contacts = ode.collide(geom1, geom2)
        self.world,self.contactgroup = args
        for c in contacts:
            c.setBounce(1)
            c.setMu(5000)
            j = ode.ContactJoint(self.world, self.contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())
  
    def _createScene(self):
        "Prepare the scene. All logic should go here"
        #draw_stars(self.screen, self.stars, black)
        #move_stars(self.stars)
        #draw_stars(self.screen, self.stars, white)
##        try:
##            print self.rayBody.getPosition()
##        except:
##            pass
        
        self.camera.setPosition(self.cameraBody.getPosition())
        for i in range(len(self.bodies)):
            #print self.bodies[i]
            #print self.sceneNodes[i]
            #self.bodies[i].setPosition(self.sceneNodes[i].getPosition())
            self.sceneNodes[i+1].setPosition(self.bodies[i].getPosition())
            self.sceneNodes[i+1].setOrientation(self.bodies[i].getQuaternion())
            if self.bodies[i].getLinearVel()[1] < .05:
                friction = ogre.Vector3(self.bodies[i].getLinearVel()[0]*.999, self.bodies[i].getLinearVel()[1], self.bodies[i].getLinearVel()[2]*.999)
                self.bodies[i].setLinearVel(friction)
                #r = self.bodies[i].getRotation()
                #friction = (r[0]*999, r[1], r[2]*999, r[3], r[4]*999, r[5], r[6]*999, r[7], r[8]*999)
                #self.bodies[i].setRotation(friction)

        if self.selection:
            if not self.selectedShape == "light":
                self.selected.showBoundingBox(True)
            pos = ogre.Vector3(0, 0, 0)
            pos.z -= self.distance
            pos = self.camera.getOrientation() * pos
            pos += self.camera.getPosition()
            self.selected.setPosition(pos)

        if self.rayOn:
            #print self.rayBody.getPosition()
            self.testNode.setPosition(self.rayBody.getPosition())
            
  
    def _presentScene(self):
        "Render the scene and anything else needed done at the time of presentation"
        ogre.WindowEventUtilities().messagePump()
        self.root.renderOneFrame()
        
        n = 2

        for i in range(n):
            self.space.collide((self.world,self.contactgroup), self.near_callback)
            self.world.step(self.dt)
            self.contactgroup.empty()

        self.lasstime = time.time()

        self.cameraBody.setLinearVel((0,self.cameraBody.getLinearVel()[1],0))
        
  
    def run(self):
        "Brings the application to life"
        sceneManager = self.sceneManager
        sceneManager.ambientLight = ogre.ColourValue(0.5, 0.5, 0.5)
        #self.sceneManager.setSkyDome(True, "Examples/CloudySky", 5, 8)

        #Set some variables
        self.visible = False
        self.rotate = 0.13
        self.raySceneQuery = self.sceneManager.createRayQuery(ogre.Ray())
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        #Grab variables
        self.selected = None
        self.selection = False
        self.selectedEnt = None
        self.selectedShape = ""
        self.distance = 1000
        self.rayOn = False
        self.rayBody = None

        #Pygame
        #pygame.display.update()
        #pygame.display.flip()
                
        # Need a light
        self.sceneManager.setAmbientLight((0.5, 0.5, 0.5))
        #(20, 200, 50)
        self.lightCount = 0
        #self.lights = [self.sceneManager.createLight('MainLight'+str(self.lightCount))]
        #self.lightCount += 1
        #self.lights[len(self.lights)-1].setPosition (20, 200, 50)
        self.lights = []
        while self._processEvents():
            self._createScene()
            self._presentScene()
            #self.clock.tick(50)
        pygame.quit()
  
    def _processEvents(self):
        "Process events and take appropriate action"
        x, y = pygame.mouse.get_rel()
        if(pygame.event.get_grab()):
            self.camera.yaw(ogre.Degree(-self.rotate * x).valueRadians())
            self.camera.pitch(ogre.Degree(-self.rotate * y).valueRadians())
            
        for event in pygame.event.get():
            pygame.key.set_repeat(1,1)
            if event.type is pygame.QUIT:
                return False
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_ESCAPE:
                return False
##            elif event.type is  pygame.MOUSEBUTTONDOWN and event.button is 1:
##                mousePos = pygame.mouse.get_pos()
##                mouseRay = self.camera.getCameraToViewportRay(mousePos[0] / float(800),
##                                                              mousePos[1] / float(600))
##                self.raySceneQuery.setRay(mouseRay)
##                self.raySceneQuery.setSortByDistance(True)
##                result = self.raySceneQuery.execute()
##                if len(result) > 0:
##                    for item in result:
##                        print item
            
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_l:
                if not self.selection:
                    self.lights.append(self.sceneManager.createLight('MainLight'+str(self.lightCount)))
                    self.lightCount += 1
                    self.selected = self.lights[len(self.lights)-1]
                    self.lights[len(self.lights)-1].setSpecularColour(ogre.ColourValue(0.0, 1.0, 1.0, 1.0))
                    self.lights[len(self.lights)-1].setDiffuseColour(ogre.ColourValue(0.0, 1.0, 1.0, 1.0))
                    self.selection = True
                    self.selectedShape = "light"

            elif event.type is pygame.MOUSEBUTTONDOWN and event.button is 5:
                if self.selection:
                    if self.selectedShape == "light":
                        color = self.selected.getDiffuseColour()
                        if color.r == 1.0:
                            color.r = 1
                            print "red"
                            if color.b <= 1.0 and color.b > 0:
                                color.b -= 0.05
                            elif color.b <= 0 and color.g == 0:
                                color.b = 0
                                color.g += 0.05
                            elif color.g < 1.0 and color.g >= 0.0:
                                color.g += 0.05
                            elif color.g > 0.95:
                                color.g = 1.0
                                color.r -= 0.05
                        elif color.g > 0.95:
                            color.g = 1
                            print "green"
                            if color.r <= 1.0 and color.r > 0:
                                color.r -= 0.05
                            elif color.r <= 0 and color.b == 0:
                                color.r = 0
                                color.b += 0.05
                            elif color.b < 1.0 and color.b >= 0.0:
                                color.b += 0.05
                            elif color.b > 0.95:
                                color.b = 1.0
                                color.g -= 0.05
                        elif color.b > 0.95:
                            color.b = 1
                            print "blue"
                            if color.g <= 1.0 and color.g > 0:
                                color.g -= 0.05
                            elif color.g <= 0 and color.r == 0:
                                color.g = 0
                                color.r += 0.05
                            elif color.r < 1.0 and color.r >= 0.0:
                                color.r += 0.05
                            elif color.r > 0.95:
                                color.r = 1.0
                                color.b -= 0.05
                                
                        #print color
                        self.selected.setSpecularColour(color)
                        self.selected.setDiffuseColour(color)
                        print self.selected.getSpecularColour()
                        print self.selected.getDiffuseColour()
            
            elif event.type is  pygame.MOUSEBUTTONDOWN and event.button is 1:
                if self.selection:
                    body = ode.Body(self.world)
                    M = ode.Mass()
                    if self.selectedShape == "sphere":
                        M.setSphere(5, self.selectedEnt.getBoundingBox().getHalfSize().x)
                        geom = ode.GeomSphere(self.space, self.selectedEnt.getBoundingBox().getHalfSize().x)
                    elif self.selectedShape == "cube":
                        size = self.entities[len(self.entities)-1].getBoundingBox().getSize().x
                        M.setBox(100, size, size, size)
                        geom = ode.GeomBox(self.space, lengths=(size, size, size))
                    body.setMass(M)
                    geom.setBody(body)
                    self.bodies.append(body)
                    self.geoms.append(geom)
                    body.setPosition(self.selected.getPosition())
                    
                    self.selected.showBoundingBox(False)
                    self.selected = None
                    self.selection = False
                    self.distance = 1000

                    vect = ogre.Vector3(0, 0, 0)
                    vect.z -= .5
                    vect = self.camera.getOrientation() * vect
                    vect *= 700
                    body.setLinearVel(vect)

                else:
                    mouseRay = self.camera.getCameraToViewportRay(400 / 800.0, 300 / 600.0)
                    self.raySceneQuery.setRay(mouseRay)
                    self.raySceneQuery.setSortByDistance(True)
                    result = self.raySceneQuery.execute()
##                else:
##                    if not self.rayOn:
##                        self.rayOn = True
##                        self.rayBody = ode.Body(self.world)
##                        M = ode.Mass()
##                        M.setSphere(2, 1)
##                        geom = ode.GeomSphere(self.space, 1)
##                        self.rayBody.setMass(M)
##                        geom.setBody(self.rayBody)
##                        self.rayBody.name = "ray"
##                        self.rayBody.setPosition(self.camera.getPosition())
##                        self.geoms.append(geom)
##
##                        vect = ogre.Vector3(0, 0, 0)
##                        vect.z -= .5
##                        vect = self.camera.getOrientation() * vect
##                        vect *= 200
##                        self.rayBody.setLinearVel(vect)
                        
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_i:
                pygame.event.set_grab(not pygame.event.get_grab())
                self.visible = not self.visible
                pygame.mouse.set_visible(self.visible)
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_SPACE:
                if self.cameraBody.getLinearVel()[1] > -10:
                    jumpVec = ogre.Vector3(self.cameraBody.getLinearVel()[0], 25, self.cameraBody.getLinearVel()[2])
                    self.cameraBody.setLinearVel(jumpVec)
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_r:
                if not self.selectedShape == "light":
                    body = ode.Body(self.world)
                    M = ode.Mass()
                    if self.selectedShape == "sphere":
                        M.setSphere(5, self.selectedEnt.getBoundingBox().getHalfSize().x)
                        geom = ode.GeomSphere(self.space, self.selectedEnt.getBoundingBox().getHalfSize().x)
                        geom.name = "sphere" + str(self.sphereCount)
                    elif self.selectedShape == "cube":
                        size = self.entities[len(self.entities)-1].getBoundingBox().getSize().x
                        M.setBox(100, size, size, size)
                        geom = ode.GeomBox(self.space, lengths=(size, size, size))
                        geom.name = "cube" + str(self.cubeCount)
                    body.setMass(M)
                    geom.setBody(body)
                    self.bodies.append(body)
                    self.geoms.append(geom)
                    body.setPosition(self.selected.getPosition())
                    
                    self.selected.showBoundingBox(False)
                self.selected = None
                self.selection = False
                self.distance = 1000
                self.selectedShape = ""
                
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_1:
                if not self.selection:
                    self.entities.append(self.sceneManager.createEntity("cube"+str(self.cubeCount), "cube.mesh"))
                    self.entities[len(self.entities)-1].setMaterialName('Examples/Hilite/Yellow')
                    pos = ogre.Vector3(0, 0, 0)
                    pos.z -= 1000
                    pos = self.camera.getOrientation() * pos
                    pos += self.camera.getPosition()
                    #pos.y += 200
                    self.sceneNodes.append(self.sceneManager.getRootSceneNode().createChildSceneNode("cubeNode"+str(self.cubeCount),pos))
                    self.cubeCount += 1
                    self.sceneNodes[len(self.sceneNodes)-1].attachObject(self.entities[len(self.entities)-1])

                    self.selected = self.sceneNodes[len(self.sceneNodes)-1]
                    self.selection = True
                    self.selectedEnt = self.entities[len(self.entities)-1]
                    self.selectedShape = "cube"
                
            elif event.type is pygame.KEYDOWN and event.key is pygame.K_2:
                if not self.selection:
                    self.entities.append(self.sceneManager.createEntity("sphere"+str(self.sphereCount), "sphere.mesh"))
                    self.entities[len(self.entities)-1].setMaterialName('Examples/Hilite/Red')
                    pos = ogre.Vector3(0, 0, 0)
                    pos.z -= 1000
                    pos = self.camera.getOrientation() * pos
                    pos += self.camera.getPosition()
                    #pos.y += 200
                    self.sceneNodes.append(self.sceneManager.getRootSceneNode().createChildSceneNode("sphere"+str(self.sphereCount),pos))
                    self.sphereCount += 1
                    self.sceneNodes[len(self.sceneNodes)-1].attachObject(self.entities[len(self.entities)-1])

                    self.selected = self.sceneNodes[len(self.sceneNodes)-1]
                    self.selection = True
                    self.selectedEnt = self.entities[len(self.entities)-1]
                    self.selectedShape = "sphere"

        pressed_keys = pygame.key.get_pressed()

        if self.selection:
            if pressed_keys[pygame.K_e]:
                self.distance += .5
            if pressed_keys[pygame.K_q]:
                self.distance -= .5

        transVector = ogre.Vector3(0, 0, 0)
        if pressed_keys[pygame.K_w]:
            transVector.z -= .5
        if pressed_keys[pygame.K_a]:
            transVector.x -= .5
        if pressed_keys[pygame.K_s]:
            transVector.z += .5
        if pressed_keys[pygame.K_d]:
            transVector.x += .5
        transVector = self.camera.getOrientation() * transVector
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_a] or pressed_keys[pygame.K_s] or pressed_keys[pygame.K_d]:
            transVector *= 50
            transVector.y = self.cameraBody.getLinearVel()[1]
            self.cameraBody.setLinearVel(transVector)
        
        return True
  
# Instantiate and run!
app = PyGameOGREApp()
app.run()
