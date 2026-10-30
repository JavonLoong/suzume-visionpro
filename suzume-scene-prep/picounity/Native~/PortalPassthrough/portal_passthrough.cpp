#include "openxr/openxr.h"
#include <android/log.h>
#include <cstdint>
#include <cstring>
#include <cstddef>

#define PORTAL_API extern "C" __attribute__((visibility("default")))
#define PORTAL_LOG(...) __android_log_print(ANDROID_LOG_INFO,"PortalComposition",__VA_ARGS__)

static PFN_xrGetInstanceProcAddr nextGetProc=nullptr;
static PFN_xrEndFrame nextEndFrame=nullptr;
static uint64_t previousSignature=~uint64_t(0);
static_assert(offsetof(XrCompositionLayerProjection,layerFlags)==16,"Unexpected OpenXR ABI");
static_assert(sizeof(XrCompositionLayerProjection)==48,"Unexpected projection layout");
static_assert(sizeof(XrFrameEndInfo)==40,"Unexpected frame layout");

static XrResult XRAPI_CALL PortalEndFrame(XrSession session,const XrFrameEndInfo* info)
{
    if(!nextEndFrame) return XR_ERROR_FUNCTION_UNSUPPORTED;
    if(!info || info->layerCount>64 || (info->layerCount && !info->layers)) return nextEndFrame(session,info);
    const XrCompositionLayerBaseHeader* layers[64];
    XrCompositionLayerProjection projections[64];
    uint32_t count=0,projectionCount=0,passthroughCount=0,changed=0;
    uint64_t signature=131+uint64_t(info->environmentBlendMode);
    for(uint32_t i=0;i<info->layerCount;i++)
    {
        const auto* layer=info->layers[i];
        if(!layer) { layers[count++]=layer;continue; }
        signature=signature*131+uint64_t(layer->type)*17+layer->layerFlags;
        const bool passthrough=layer->type==XR_TYPE_COMPOSITION_LAYER_PASSTHROUGH_FB;
        if(passthrough) passthroughCount++;
        if(layer->type==XR_TYPE_COMPOSITION_LAYER_PROJECTION)
        {
            projectionCount++;
            auto& copy=projections[i];
            copy=*reinterpret_cast<const XrCompositionLayerProjection*>(layer);
            if(!(copy.layerFlags&XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT)) changed++;
            copy.layerFlags|=XR_COMPOSITION_LAYER_BLEND_TEXTURE_SOURCE_ALPHA_BIT;
            layers[count++]=reinterpret_cast<const XrCompositionLayerBaseHeader*>(&copy);
            continue;
        }
        layers[count++]=layer;
    }
    const bool log=signature!=previousSignature;
    if(log)
    {
        previousSignature=signature;
        PORTAL_LOG("stable env=%d input=%u projection=%u passthrough=%u output=%u alphaFlagsRepaired=%u",
            int(info->environmentBlendMode),info->layerCount,projectionCount,passthroughCount,count,changed);
        for(uint32_t i=0;i<info->layerCount;i++)
            if(info->layers[i]) PORTAL_LOG("inputLayer[%u] type=%d flags=0x%llx",i,int(info->layers[i]->type),(unsigned long long)info->layers[i]->layerFlags);
    }
    XrFrameEndInfo copy=*info;
    copy.layerCount=count;copy.layers=layers;
    XrResult result=nextEndFrame(session,&copy);
    if(log || XR_FAILED(result)) PORTAL_LOG("xrEndFrame result=%d",int(result));
    return result;
}

static XrResult XRAPI_CALL PortalGetProc(XrInstance instance,const char* name,PFN_xrVoidFunction* function)
{
    if(!nextGetProc) return XR_ERROR_FUNCTION_UNSUPPORTED;
    XrResult result=nextGetProc(instance,name,function);
    if(XR_SUCCEEDED(result) && name && function && *function && std::strcmp(name,"xrEndFrame")==0)
    {
        if(*function!=reinterpret_cast<PFN_xrVoidFunction>(PortalEndFrame))
            nextEndFrame=reinterpret_cast<PFN_xrEndFrame>(*function);
        *function=reinterpret_cast<PFN_xrVoidFunction>(PortalEndFrame);
    }
    return result;
}

PORTAL_API PFN_xrGetInstanceProcAddr Portal_Hook(PFN_xrGetInstanceProcAddr original)
{
    if(original!=PortalGetProc) nextGetProc=original;
    nextEndFrame=nullptr;previousSignature=~uint64_t(0);
    PORTAL_LOG("OpenXR final composition hook installed");
    return PortalGetProc;
}
