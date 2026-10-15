// Original recorded/synthesized assets. One context, shared loops, no microphone access.
const clamp = value => Math.max(0, Math.min(1, Number(value) || 0));
const DEFAULT_MIX = Object.freeze({volume:.65,musicVolume:.4,sfxVolume:.8,ambienceVolume:.3});
const GRILL_POSITION = [3.25,1.03,-8.2];

export function createManagementAudio({onStatus=()=>{},fetcher=globalThis.fetch?.bind(globalThis),AudioContextClass=globalThis.AudioContext||globalThis.webkitAudioContext,manifestURL='./assets/audio/management_v1/manifest.json'}={}) {
  let context=null,master=null,previewMaster=null,buses=null,manifest=null,loading=null,startPending=null,resumePending=null,suspendPending=null,outputAnalyser=null,outputSamples=null;
  let disposed=false,unlocked=false,loaded=false,status='locked',error='',lastSound='',dropped=0,deduped=0,previewUntil=0;
  let state=null,view={menu:true,paused:false,hidden:false,blocking:true,player:null,dt:0},mix={...DEFAULT_MIX};
  let lastPlayer=null,stepDistance=0,lastStep=-Infinity,stepCount=0,grillLevel=0,grillPan=0,duckUntil=0;
  const buffers=new Map(),loops=new Map(),shots=new Set(),recent=new Map(),played={};
  const targets={menu:0,service:0,rush:0,room:0,grill_sizzle:0,master:0};
  const musicNames=['menu','service','rush'];
  const now=()=>context?.currentTime||0;
  function report(next,message) {status=next;onStatus({status:next,message});}
  function parameter(param,value,seconds=.15) {
    if(!param||Math.abs((param._dinerTarget??param.value)-value)<.002)return;
    param._dinerTarget=value;
    if(param.cancelAndHoldAtTime)param.cancelAndHoldAtTime(now());
    else {param.cancelScheduledValues?.(now());param.setValueAtTime?.(param.value,now());}
    if(seconds>0)param.setTargetAtTime(value,now(),seconds);else param.setValueAtTime(value,now());
  }
  function createContext() {
    if(context)return;
    if(!AudioContextClass)throw new Error('Audio is not supported by this browser.');
    context=new AudioContextClass();
    if(context.createAnalyser){outputAnalyser=context.createAnalyser();outputAnalyser.fftSize=256;outputSamples=new Float32Array(256);outputAnalyser.connect(context.destination);}
    master=context.createGain();master.gain.value=0;master.connect(outputAnalyser||context.destination);
    previewMaster=context.createGain();previewMaster.gain.value=mix.volume;previewMaster.connect(outputAnalyser||context.destination);
    buses={music:context.createGain(),sfx:context.createGain(),ambience:context.createGain()};
    for(const bus of Object.values(buses))bus.connect(master);
    setMix(mix);
  }
  async function resumeContext() {
    if(!context||view.hidden||disposed)return;
    if(resumePending)return resumePending;
    resumePending=(async()=>{
      if(context.state==='suspended')await context.resume();
      if(context.state!=='running')throw new Error('Sound is blocked. Click Test Audio to try again.');
      unlocked=true;
    })();
    try {await resumePending;} finally {resumePending=null;}
  }
  async function loadAssets() {
    if(loaded)return;
    if(loading)return loading;
    loading=(async()=>{
      if(!fetcher)throw new Error('Audio files could not be loaded.');
      if(!manifest){const response=await fetcher(manifestURL);if(!response.ok)throw new Error('Audio manifest could not be loaded.');manifest=await response.json();setMix(mix);}
      if(!manifest.music?.menu||!manifest.music?.service||!manifest.music?.rush||!manifest.sfx?.grill_sizzle||!manifest.ambience?.room)throw new Error('Audio manifest is incomplete.');
      const entries=[...Object.entries(manifest.music).map(([id,item])=>({id,item,bus:'music'})),...Object.entries(manifest.sfx).map(([id,item])=>({id,item,bus:'sfx'})),...Object.entries(manifest.ambience).map(([id,item])=>({id,item,bus:'ambience'}))];
      const missing=entries.filter(entry=>!buffers.has(entry.id));
      const results=await Promise.allSettled(missing.map(async entry=>{
        const response=await fetcher(entry.item.url);if(!response.ok)throw new Error(entry.id);
        const buffer=await context.decodeAudioData(await response.arrayBuffer());
        buffers.set(entry.id,{...entry,buffer});
      }));
      const failed=results.filter(result=>result.status==='rejected');
      if(disposed)throw new Error('Audio has closed.');
      if(failed.length)throw new Error(`${failed.length} sound file${failed.length===1?'':'s'} could not load. Click Test Audio to retry.`);
      const service=buffers.get('service').buffer.duration,rush=buffers.get('rush').buffer.duration;
      if(Math.abs(service-rush)>.025)throw new Error('The service music layers could not synchronize.');
      loaded=true;createLoops();
    })();
    try {await loading;} finally {loading=null;}
  }
  function createLoops() {
    const when=now()+.05;
    for(const id of [...musicNames,'room','grill_sizzle']) {
      if(loops.has(id))continue;
      const entry=buffers.get(id);if(!entry)continue;
      const source=context.createBufferSource(),gain=context.createGain();
      source.buffer=entry.buffer;source.loop=true;source.loopStart=0;source.loopEnd=Number(entry.item.seconds)||entry.buffer.duration;
      gain.gain.value=0;source.connect(gain);
      let pan=null;
      if(id==='grill_sizzle'&&context.createStereoPanner){pan=context.createStereoPanner();gain.connect(pan);pan.connect(buses.ambience);}else gain.connect(buses[entry.bus]);
      source.start(when,0);loops.set(id,{source,gain,pan});
    }
    applyState();
  }
  async function start() {
    if(disposed)throw new Error('Audio has closed.');
    if(startPending)return startPending;
    try {createContext();} catch(cause){error=cause.message;report('error',error);throw cause;}
    startPending=(async()=>{
      try {
        // resume happens within the actual input gesture, before network/decode awaits.
        await resumeContext();
        if(!loaded)report('loading','Loading diner sounds…');
        await loadAssets();
        if(disposed)throw new Error('Audio has closed.');
        if(!unlocked)throw new Error('Click Test Audio to enable sound.');
        error='';applyState();report('ready',mix.volume===0?'Sound muted.':'Sound ready.');
      }catch(cause){if(!disposed){error=cause.message;report('error',error);}throw cause;}
    })();
    try {await startPending;} finally {startPending=null;}
  }
  function setMix(next={}) {
    for(const key of Object.keys(DEFAULT_MIX))if(Object.hasOwn(next,key))mix[key]=clamp(next[key]);
    if(buses){parameter(buses.music.gain,mix.musicVolume*(manifest?.mix?.musicBus??1));parameter(buses.sfx.gain,mix.sfxVolume);parameter(buses.ambience.gain,mix.ambienceVolume);parameter(previewMaster.gain,mix.volume);applyState();}
  }
  function spatial(position) {
    const player=view.player;
    if(!Array.isArray(position)||!Array.isArray(player))return {volume:1,pan:0};
    const dx=position[0]-player[0],dz=position[2]-player[2],distance=Math.hypot(dx,dz);
    const yaw=Number(view.yaw)||0,right=dx*Math.cos(yaw)-dz*Math.sin(yaw);
    return {volume:1/(1+distance*.3),pan:Math.max(-.85,Math.min(.85,right/Math.max(2,distance)))};
  }
  function clearShots() {for(const shot of [...shots]){try{shot.source.stop();}catch{}shot.cleanup();}}
  function spawnShot(id,{position,volume=1,delay=0,preview=false,duration}={}) {
    const entry=buffers.get(id);if(!entry)return false;
    const source=context.createBufferSource(),gain=context.createGain(),space=spatial(position);
    source.buffer=entry.buffer;gain.gain.value=(entry.item.gain??1)*clamp(volume)*space.volume*(preview?(entry.bus==='music'?mix.musicVolume*(manifest?.mix?.musicBus??1):mix.sfxVolume):1);
    source.connect(gain);let pan=null;
    if(position&&context.createStereoPanner){pan=context.createStereoPanner();pan.pan.value=space.pan;gain.connect(pan);pan.connect(preview?previewMaster:buses[entry.bus]);}else gain.connect(preview?previewMaster:buses[entry.bus]);
    const shot={source,cleanup(){if(!shots.delete(shot))return;source.disconnect();gain.disconnect();pan?.disconnect();}};
    shots.add(shot);source.onended=shot.cleanup;
    if(duration)source.start(now()+delay,0,duration);else source.start(now()+delay);
    lastSound=id;played[id]=(played[id]||0)+1;return true;
  }
  function play(id,{dedupe,position,volume=1,...options}={}) {
    if(disposed||!loaded||!unlocked||context?.state!=='running'||view.hidden||view.paused){dropped++;return false;}
    const time=now(),cooldown=id==='wrong_action'?.75:id==='ui_click'?.07:0;
    const token=dedupe?`${id}:${dedupe}`:cooldown?`cooldown:${id}`:null;
    if(token&&recent.has(token)&&(dedupe||time-recent.get(token)<cooldown)){deduped++;return false;}
    if(token){recent.set(token,time);if(recent.size>128)recent.delete(recent.keys().next().value);}
    if(['food_ready','food_burnt','serve_cash','wrong_action'].includes(id)){duckUntil=time+.8;applyState();}
    return spawnShot(id,{position,volume,...options});
  }
  function applyState() {
    if(!context)return;
    const silent=view.hidden||view.paused||previewUntil>now();
    targets.master=silent?0:mix.volume;parameter(master.gain,targets.master,.08);
    parameter(buses.music.gain,mix.musicVolume*(manifest?.mix?.musicBus??1)*(now()<duckUntil?.52:1),now()<duckUntil?.05:.25);
    const management=state?.kind==='management',business=management&&['open','closing'].includes(state.phase);
    const menu=view.menu||!business;
    const busy=!menu&&(state.orders||[]).filter(order=>order.status==='waiting').length>=2;
    targets.menu=menu?1:0;targets.service=menu?0:busy?0:1;targets.rush=busy?1:0;
    targets.room=business&&!view.menu&&!view.paused&&!view.hidden?1:0;
    const cooking=business&&!view.menu&&!view.paused&&!view.hidden&&!view.blocking&&state.prep?.stage==='grilling';
    const space=spatial(GRILL_POSITION);grillLevel=cooking?space.volume:0;grillPan=space.pan;targets.grill_sizzle=grillLevel;
    for(const id of musicNames){const loop=loops.get(id);if(loop)parameter(loop.gain.gain,targets[id]*(buffers.get(id).item.gain??1),.6);}
    const room=loops.get('room');if(room)parameter(room.gain.gain,targets.room*(buffers.get('room').item.gain??1)*(manifest?.mix?.ambienceBus??1),.3);
    const grill=loops.get('grill_sizzle');if(grill){parameter(grill.gain.gain,grillLevel*(buffers.get('grill_sizzle').item.gain??1),.12);if(grill.pan)parameter(grill.pan.pan,grillPan,.12);}
  }
  function update(nextState,options={}) {
    state=nextState;const wasHidden=view.hidden,wasPaused=view.paused;view={...view,...options};
    if(view.paused&&!wasPaused){clearShots();previewUntil=0;lastPlayer=null;stepDistance=0;}
    const resumeVisible=()=>resumeContext().then(()=>{applyState();if(loaded)report('ready',mix.volume===0?'Sound muted.':'Sound ready.');}).catch(cause=>{error=cause.message;report('error','Click Test Audio to restore sound.');});
    if(view.hidden&&!wasHidden){clearShots();previewUntil=0;lastPlayer=null;stepDistance=0;parameter(master?.gain,0,0);if(context?.state==='running'){suspendPending=context.suspend().then(()=>{if(!view.hidden&&!disposed&&unlocked)return resumeVisible();}).catch(cause=>{error=cause.message;report('error','Sound could not pause.');}).finally(()=>{suspendPending=null;});}}
    else if(!view.hidden&&wasHidden&&unlocked&&context?.state==='suspended'&&!suspendPending)resumeVisible();
    applyState();
    const walking=loaded&&context?.state==='running'&&!view.menu&&!view.paused&&!view.hidden&&!view.blocking&&['open','closing'].includes(state?.phase);
    if(walking&&Array.isArray(view.player)&&lastPlayer){
      const distance=Math.hypot(view.player[0]-lastPlayer[0],view.player[2]-lastPlayer[2]);
      // Ignore camera resets / teleports and collision jitter; only actual travel creates steps.
      if(distance>.002&&distance<.6){stepDistance+=distance;if(stepDistance>=.68&&now()-lastStep>.22){if(play('footstep_tile',{volume:.55}))stepCount++;stepDistance%=.68;lastStep=now();}}
    }else stepDistance=0;
    lastPlayer=Array.isArray(view.player)?[...view.player]:null;
  }
  async function preview() {
    await start();if(view.hidden||disposed)return false;
    // A bounded audition uses its own master, so paused kitchen/NPC sounds stay paused.
    clearShots();previewUntil=now()+2.8;applyState();parameter(master.gain,0,0);parameter(previewMaster.gain,mix.volume,0);
    spawnShot('menu',{preview:true,duration:2.8,volume:.85});
    spawnShot('ticket_paper',{preview:true,delay:.25});spawnShot('onion_crunch',{preview:true,delay:.85});spawnShot('serve_cash',{preview:true,delay:1.4});
    return true;
  }
  function getDiagnostics() {
    const audible=loaded&&unlocked&&context?.state==='running'&&!view.hidden&&!view.paused&&targets.master>0;
    const activeLoops=[...loops.keys()].filter(id=>audible&&targets[id]>0&&(musicNames.includes(id)?mix.musicVolume:mix.ambienceVolume)>0);
    let outputRms=0,outputPeak=0;if(outputAnalyser&&outputSamples&&context?.state==='running'){outputAnalyser.getFloatTimeDomainData(outputSamples);for(const value of outputSamples){outputRms+=value*value;outputPeak=Math.max(outputPeak,Math.abs(value));}outputRms=Math.sqrt(outputRms/outputSamples.length);}
    return {status,error,unlocked,loaded,contextState:context?.state||'not-created',manifest:manifestURL,mix:{...mix},hidden:!!view.hidden,paused:!!view.paused,blocking:!!view.blocking,mode:view.menu||!['open','closing'].includes(state?.phase)?'menu':targets.rush?'rush':'service',music:musicNames.filter(id=>audible&&mix.musicVolume>0&&targets[id]>0),musicTargets:Object.fromEntries(musicNames.map(id=>[id,targets[id]])),loopCount:loops.size,activeLoops,gainLevels:{master:targets.master,music:buses?.music.gain._dinerTarget??0,sfx:buses?.sfx.gain._dinerTarget??0,ambience:buses?.ambience.gain._dinerTarget??0,loops:Object.fromEntries([...loops].map(([id,loop])=>[id,loop.gain.gain._dinerTarget??0]))},loadedMusic:musicNames.filter(id=>buffers.has(id)).length,loadedSfx:Object.keys(manifest?.sfx||{}).filter(id=>buffers.has(id)).length,loadedAmbience:Object.keys(manifest?.ambience||{}).filter(id=>buffers.has(id)).length,grillActive:audible&&mix.ambienceVolume>0&&grillLevel>0,grillLevel,grillPan,roomActive:audible&&mix.ambienceVolume>0&&targets.room>0,footsteps:stepCount,lastSound,played:{...played},activeOneShots:shots.size,droppedEvents:dropped,dedupedEvents:deduped,preview:context?.state==='running'&&!view.hidden&&previewUntil>now(),outputRms,outputPeak,disposed};
  }
  function dispose() {
    if(disposed)return;disposed=true;clearShots();for(const loop of loops.values()){try{loop.source.stop();}catch{}loop.source.disconnect();loop.gain.disconnect();loop.pan?.disconnect();}loops.clear();master?.disconnect();previewMaster?.disconnect();outputAnalyser?.disconnect();for(const bus of Object.values(buses||{}))bus.disconnect();context?.close();report('closed','Sound closed.');
  }
  return {start,play,setMix,update,preview,dispose,getDiagnostics};
}
