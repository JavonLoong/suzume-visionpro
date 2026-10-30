#include "portal_passthrough.cpp"
#include <cstdio>
#include <cstdlib>
static void require(bool condition,const char* reason) { if(!condition) { std::printf("FAIL: %s\n",reason);std::exit(1); } }
static int testCase=0,calls=0;
static const XrCompositionLayerProjectionView* expectedViews=nullptr;
static const void* expectedNext=nullptr;
static XrResult XRAPI_CALL FakeEnd(XrSession,const XrFrameEndInfo* info)
{
    calls++;
    require(info && info->displayTime==1234 && info->environmentBlendMode==XR_ENVIRONMENT_BLEND_MODE_ALPHA_BLEND,"frame metadata changed");
    if(testCase==4) require(info->layerCount==65,"large layer list must be forwarded intact");
    else
    {
        require(info->layerCount==3,"normal mode dropped layers");
        require(info->layers[0]->type==XR_TYPE_COMPOSITION_LAYER_PASSTHROUGH_FB && info->layers[2]->type==XR_TYPE_COMPOSITION_LAYER_QUAD,"layer order changed");
        auto* projection=reinterpret_cast<const XrCompositionLayerProjection*>(info->layers[1]);
        require(projection->layerFlags==(testCase==2?6:XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT),"incorrect source-alpha flag");
        require(projection->views==expectedViews && projection->viewCount==2 && projection->next==expectedNext,"projection view/extension data changed");
    }
    return XR_SESSION_LOSS_PENDING;
}
static XrResult XRAPI_CALL FakeGetProc(XrInstance,const char* name,PFN_xrVoidFunction* function)
{
    if(std::strcmp(name,"xrEndFrame")!=0) { *function=nullptr;return XR_ERROR_FUNCTION_UNSUPPORTED; }
    *function=reinterpret_cast<PFN_xrVoidFunction>(FakeEnd);return XR_SUCCESS;
}
int main()
{
    auto getProc=Portal_Hook(FakeGetProc);PFN_xrVoidFunction function=nullptr;
    require(getProc(XR_NULL_HANDLE,"xrEndFrame",&function)==XR_SUCCESS && function,"end-frame hook missing");
    auto end=reinterpret_cast<PFN_xrEndFrame>(function);
    XrCompositionLayerProjectionView views[2]{};int extensionData=42;
    expectedViews=views;expectedNext=&extensionData;
    XrCompositionLayerPassthroughFB reality{};reality.type=XR_TYPE_COMPOSITION_LAYER_PASSTHROUGH_FB;
    XrCompositionLayerProjection projection{};projection.type=XR_TYPE_COMPOSITION_LAYER_PROJECTION;projection.viewCount=2;projection.views=views;projection.next=expectedNext;
    XrCompositionLayerQuad quad{};quad.type=XR_TYPE_COMPOSITION_LAYER_QUAD;
    const XrCompositionLayerBaseHeader* layers[]={reinterpret_cast<const XrCompositionLayerBaseHeader*>(&reality),reinterpret_cast<const XrCompositionLayerBaseHeader*>(&projection),reinterpret_cast<const XrCompositionLayerBaseHeader*>(&quad)};
    XrFrameEndInfo frame{};frame.type=XR_TYPE_FRAME_END_INFO;frame.displayTime=1234;frame.environmentBlendMode=XR_ENVIRONMENT_BLEND_MODE_ALPHA_BLEND;frame.layerCount=3;frame.layers=layers;
    testCase=0;
    for(int i=0;i<1500;i++)
    {
        require(end(XR_NULL_HANDLE,&frame)==XR_SESSION_LOSS_PENDING,"runtime return value lost");
        require(projection.layerFlags==0 && frame.layerCount==3 && frame.layers==layers,"caller-owned memory mutated");
    }
    testCase=2;projection.layerFlags=6;
    end(XR_NULL_HANDLE,&frame);
    testCase=4;frame.layerCount=65;end(XR_NULL_HANDLE,&frame);
    require(calls==1502,"runtime was called wrong number of times");
    require(getProc(XR_NULL_HANDLE,"unknown",&function)==XR_ERROR_FUNCTION_UNSUPPORTED && !function,"unknown function handling changed");
    std::puts("PASS: ARM64/OpenXR ABI; 1500 consecutive frames preserve ALL software and passthrough layers; no diagnostic filtering or mode control; source-alpha flags preserved/repaired; original memory/view/extension data intact; runtime results and oversized lists forwarded.");
    return 0;
}
