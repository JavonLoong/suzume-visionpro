    const steelFit25=__STEEL_FIT_25__;
    function steelMaterial25(edge=false){
      const m=new T.MeshStandardMaterial({color:0xffffff,roughness:.90,metalness:.12});
      const palette=(edge?[0x41433b,0x6f6450,0x958265,0xa17a51]:[0x3b403c,0x655d4d,0x8a7756,0xa1774b]).map(hex=>new T.Color(hex).convertSRGBToLinear().toArray());
      m.customProgramCacheKey=()=>edge?'steel-oxide-v25-edge':'steel-oxide-v25-main';
      m.onBeforeCompile=shader=>{
        shader.vertexShader='varying vec3 vSteelPosition25;\n'+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvSteelPosition25=(modelMatrix*vec4(transformed,1.0)).xyz;');
        shader.fragmentShader=`varying vec3 vSteelPosition25;
          float steelHash25(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
          float steelNoise25(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(mix(steelHash25(i),steelHash25(i+vec3(1,0,0)),f.x),mix(steelHash25(i+vec3(0,1,0)),steelHash25(i+vec3(1,1,0)),f.x),f.y),mix(mix(steelHash25(i+vec3(0,0,1)),steelHash25(i+vec3(1,0,1)),f.x),mix(steelHash25(i+vec3(0,1,1)),steelHash25(i+vec3(1,1,1)),f.x),f.y),f.z);}
          float steelFbm25(vec3 p){float value=0.0,a=.5333;for(int i=0;i<4;i++){value+=a*steelNoise25(p);p=p*2.01+vec3(7.3,2.1,5.6);a*=.5;}return value;}
          `+shader.fragmentShader;
        const rgb=palette.map(a=>'vec3('+a.map(v=>v.toFixed(8)).join(',')+')');
        shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
          float oxide25=steelFbm25(vSteelPosition25*3.5);
          vec3 color25=mix(${rgb[0]},${rgb[1]},smoothstep(.20,.40,oxide25));
          color25=mix(color25,${rgb[2]},smoothstep(.40,.58,oxide25));
          color25=mix(color25,${rgb[3]},smoothstep(.58,.78,oxide25));
          diffuseColor.rgb=color25*(.94+.12*steelNoise25(vSteelPosition25*85.0));`);
      };
      return m;
    }
    const steelMaterials25={steel:steelMaterial25(),edge:steelMaterial25(true),concrete:new T.MeshStandardMaterial({color:0x77766d,roughness:.95})};
    for(const [name,color]of Object.entries({vine:0x536238,leaf0:0x58752b,leaf1:0x70953c,leaf2:0xa1b359}))steelMaterials25[name]=new T.MeshStandardMaterial({color,roughness:.90});
    let removedSteel25=0;
    for(const o of [...scene.children])if(o.name.startsWith('Broken radial dome steelwork solid mesh')){scene.remove(o);removedSteel25++;}
    const steelGroup25=buildMovieSteel25(T,scene,steelFit25,steelMaterials25),steelParts25=bake(steelGroup25);
    root.steelEvidence25={revision:25,parts:steelParts25,removedLegacyBatches:removedSteel25,actualISections:true,completeRadialRing:true,inferredHiddenStructure:true,browserRuntimeVerified:false,oneToOneComplete:false};
