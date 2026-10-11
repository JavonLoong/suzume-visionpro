    const shoreFit26=__SHORE_FIT_26__;
    const shorePalettes26={concrete:[0x73877c,0x9ca993,0xbdc3a7],bank:[0x4c6762,0x748b7b,0x929e86],curb:[0x748b80,0xa4b19d,0xbec8ad],rust:[0x3f2923,0x704536,0x9c7050],rustDark:[0x302a25,0x524335,0x80644a]};
    function shoreMaterial26(role){
      const m=new T.MeshStandardMaterial({color:0xffffff,roughness:.96,metalness:role.startsWith('rust')?.12:0});
      const palette=shorePalettes26[role].map(hex=>new T.Color(hex).convertSRGBToLinear().toArray());
      m.customProgramCacheKey=()=> 'shore-material-v26-'+role;
      m.onBeforeCompile=shader=>{
        shader.vertexShader='varying vec3 vShorePosition26;\n'+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvShorePosition26=(modelMatrix*vec4(transformed,1.0)).xyz;');
        shader.fragmentShader=`varying vec3 vShorePosition26;
          float shoreHash26(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
          float shoreNoise26(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(mix(shoreHash26(i),shoreHash26(i+vec3(1,0,0)),f.x),mix(shoreHash26(i+vec3(0,1,0)),shoreHash26(i+vec3(1,1,0)),f.x),f.y),mix(mix(shoreHash26(i+vec3(0,0,1)),shoreHash26(i+vec3(1,0,1)),f.x),mix(shoreHash26(i+vec3(0,1,1)),shoreHash26(i+vec3(1,1,1)),f.x),f.y),f.z);}
          float shoreFbm26(vec3 p){float value=0.0,a=.5333;for(int i=0;i<4;i++){value+=a*shoreNoise26(p);p=p*2.01+vec3(7.3,2.1,5.6);a*=.5;}return value;}
          `+shader.fragmentShader;
        const rgb=palette.map(a=>'vec3('+a.map(v=>v.toFixed(8)).join(',')+')');
        shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
          float patina26=shoreFbm26(vShorePosition26*${role.startsWith('rust')?'3.2':'2.1'});
          vec3 color26=mix(${rgb[0]},${rgb[1]},smoothstep(.22,.49,patina26));
          color26=mix(color26,${rgb[2]},smoothstep(.49,.76,patina26));
          diffuseColor.rgb=color26*(.96+.08*shoreNoise26(vShorePosition26*65.0));`);
      };return m;
    }
    const shoreMaterials26=Object.fromEntries(Object.keys(shorePalettes26).map(role=>[role,shoreMaterial26(role)]));
    const shoreGroup26=buildMovieShore26(T,scene,shoreFit26,shoreMaterials26),shoreParts26=bake(shoreGroup26);
    root.shoreEvidence26={revision:26,parts:shoreParts26,slopedSolidSlabs:true,hollowPipeBores:true,completeCourtyardBank:true,inferredHiddenStructure:true,browserRuntimeVerified:false,oneToOneComplete:false};
