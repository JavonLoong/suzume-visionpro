"""Generate a small, dependency-free Xcode project; no Swift compilation is claimed."""
from pathlib import Path
import hashlib,json,plistlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]/'VisionProPortal'
APP=ROOT/'VisionProPortal'
objects={}
def oid(s): return hashlib.sha256(s.encode()).hexdigest()[:24].upper()
def add(key,isa,**kw):
    ref=oid(key);objects[ref]={'isa':isa,**kw};return ref
def serial(v):
    if isinstance(v,dict): return '{\n'+''.join(f'{json.dumps(k)} = {serial(x)};\n' for k,x in v.items())+'}'
    if isinstance(v,list): return '(\n'+''.join(serial(x)+',\n' for x in v)+')'
    if isinstance(v,int): return str(v)
    return json.dumps(v,ensure_ascii=False)
source_refs=[];source_build=[];resource_refs=[];resource_build=[]
for path in sorted(APP.glob('*.swift')):
    ref=add('file:'+path.name,'PBXFileReference',lastKnownFileType='sourcecode.swift',path=path.name,sourceTree='<group>')
    source_refs.append(ref);source_build.append(add('build:'+path.name,'PBXBuildFile',fileRef=ref))
for name in ('DreamWorld.usdz','DoorFrame.usdz','DoorLeaf.usdz','NightSky.png','AssetManifest.json'):
    path=APP/'Resources'/name
    assert path.is_file(),path
    kind={'.usdz':'file.usdz','.png':'image.png','.json':'text.json'}[path.suffix]
    ref=add('file:'+name,'PBXFileReference',lastKnownFileType=kind,path=name,sourceTree='<group>')
    resource_refs.append(ref);resource_build.append(add('build:'+name,'PBXBuildFile',fileRef=ref))
info={'CFBundleDevelopmentRegion':'zh_CN','CFBundleDisplayName':'铃芽之旅·梦幻门',
 'CFBundleExecutable':'$(EXECUTABLE_NAME)','CFBundleIdentifier':'$(PRODUCT_BUNDLE_IDENTIFIER)',
 'CFBundleInfoDictionaryVersion':'6.0','CFBundleName':'$(PRODUCT_NAME)','CFBundlePackageType':'APPL',
 'CFBundleShortVersionString':'$(MARKETING_VERSION)','CFBundleVersion':'$(CURRENT_PROJECT_VERSION)',
 'UIApplicationSceneManifest':{'UIApplicationSupportsMultipleScenes':True},'UILaunchScreen':{}}
(APP/'Info.plist').write_bytes(plistlib.dumps(info,sort_keys=False))
info_ref=add('Info.plist','PBXFileReference',lastKnownFileType='text.plist.xml',path='Info.plist',sourceTree='<group>')
rg=add('resource-group','PBXGroup',children=resource_refs,path='Resources',sourceTree='<group>')
sg=add('source-group','PBXGroup',children=source_refs+[info_ref,rg],path='VisionProPortal',sourceTree='<group>')
product=add('product','PBXFileReference',explicitFileType='wrapper.application',path='VisionProPortal.app',sourceTree='BUILT_PRODUCTS_DIR')
pg=add('products','PBXGroup',children=[product],name='Products',sourceTree='<group>')
main=add('main-group','PBXGroup',children=[sg,pg],sourceTree='<group>')
sources=add('sources-phase','PBXSourcesBuildPhase',buildActionMask=2147483647,files=source_build,runOnlyForDeploymentPostprocessing=0)
resources=add('resources-phase','PBXResourcesBuildPhase',buildActionMask=2147483647,files=resource_build,runOnlyForDeploymentPostprocessing=0)
frameworks=add('frameworks-phase','PBXFrameworksBuildPhase',buildActionMask=2147483647,files=[],runOnlyForDeploymentPostprocessing=0)
base={'PRODUCT_NAME':'$(TARGET_NAME)','PRODUCT_BUNDLE_IDENTIFIER':'com.javonloong.SuzumePortal',
 'INFOPLIST_FILE':'VisionProPortal/Info.plist','GENERATE_INFOPLIST_FILE':'NO','SDKROOT':'xros',
 'SUPPORTED_PLATFORMS':'xros xrsimulator','TARGETED_DEVICE_FAMILY':'7','XROS_DEPLOYMENT_TARGET':'2.0',
 'SWIFT_VERSION':'5.0','CURRENT_PROJECT_VERSION':'2','MARKETING_VERSION':'0.2','CODE_SIGN_STYLE':'Automatic',
 'LD_RUNPATH_SEARCH_PATHS':['$(inherited)','@executable_path/Frameworks']}
configs=[];projects=[]
for name in ('Debug','Release'):
    settings={**base,'SWIFT_OPTIMIZATION_LEVEL':'-Onone' if name=='Debug' else '-O'}
    if name=='Debug':settings['SWIFT_ACTIVE_COMPILATION_CONDITIONS']='DEBUG'
    configs.append(add('target-config'+name,'XCBuildConfiguration',buildSettings=settings,name=name))
    projects.append(add('project-config'+name,'XCBuildConfiguration',buildSettings={'CLANG_ENABLE_MODULES':'YES','SWIFT_COMPILATION_MODE':'singlefile' if name=='Debug' else 'wholemodule'},name=name))
tc=add('target-configs','XCConfigurationList',buildConfigurations=configs,defaultConfigurationIsVisible=0,defaultConfigurationName='Release')
pc=add('project-configs','XCConfigurationList',buildConfigurations=projects,defaultConfigurationIsVisible=0,defaultConfigurationName='Release')
target=add('target','PBXNativeTarget',buildConfigurationList=tc,buildPhases=[sources,frameworks,resources],buildRules=[],dependencies=[],name='VisionProPortal',productName='VisionProPortal',productReference=product,productType='com.apple.product-type.application')
project=add('project','PBXProject',attributes={'LastUpgradeCheck':'1600','TargetAttributes':{target:{'CreatedOnToolsVersion':'16.0'}}},buildConfigurationList=pc,compatibilityVersion='Xcode 14.0',developmentRegion='zh_CN',hasScannedForEncodings=0,knownRegions=['zh_CN','en','Base'],mainGroup=main,productRefGroup=pg,projectDirPath='',projectRoot='',targets=[target])
folder=ROOT/'VisionProPortal.xcodeproj';folder.mkdir(exist_ok=True)
(folder/'project.pbxproj').write_text('// !$*UTF8*$!\n'+serial({'archiveVersion':1,'classes':{},'objectVersion':56,'objects':objects,'rootObject':project})+'\n',encoding='utf-8')
schemes=folder/'xcshareddata'/'xcschemes';schemes.mkdir(parents=True,exist_ok=True)
root=ET.Element('Scheme',LastUpgradeVersion='1600',version='1.3')
build=ET.SubElement(root,'BuildAction',parallelizeBuildables='YES',buildImplicitDependencies='YES')
entries=ET.SubElement(build,'BuildActionEntries')
entry=ET.SubElement(entries,'BuildActionEntry',buildForTesting='YES',buildForRunning='YES',buildForProfiling='YES',buildForArchiving='YES',buildForAnalyzing='YES')
def reference(parent):return ET.SubElement(parent,'BuildableReference',BuildableIdentifier='primary',BlueprintIdentifier=target,BuildableName='VisionProPortal.app',BlueprintName='VisionProPortal',ReferencedContainer='container:VisionProPortal.xcodeproj')
reference(entry)
launch=ET.SubElement(root,'LaunchAction',buildConfiguration='Debug',selectedDebuggerIdentifier='Xcode.DebuggerFoundation.Debugger.LLDB',selectedLauncherIdentifier='Xcode.IDEFoundation.Launcher.LLDB',launchStyle='0',useCustomWorkingDirectory='NO',ignoresPersistentStateOnLaunch='NO',debugDocumentVersioning='YES',debugServiceExtension='internal',allowLocationSimulation='YES')
reference(ET.SubElement(launch,'BuildableProductRunnable',runnableDebuggingMode='0'))
ET.SubElement(root,'AnalyzeAction',buildConfiguration='Debug')
ET.SubElement(root,'ArchiveAction',buildConfiguration='Release',revealArchiveInOrganizer='YES')
ET.indent(root);ET.ElementTree(root).write(schemes/'VisionProPortal.xcscheme',encoding='utf-8',xml_declaration=True)
print(json.dumps({'project':str(folder),'swiftFiles':len(source_refs),'resources':len(resource_refs),'compiled':False},ensure_ascii=False))
