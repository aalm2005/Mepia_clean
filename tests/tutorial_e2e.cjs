// Tutorial real en Next/Edge; Auth, datos y SDK simulados. Solo loopback.
const assert=require("node:assert/strict"), fs=require("node:fs"), path=require("node:path"), net=require("node:net"), vm=require("node:vm");
const {spawn}=require("node:child_process");
const {chromium}=require(process.env.MEPIA_PLAYWRIGHT_MODULE || "playwright");
const {restoreGeneratedTypes}=require("./chat_step5_workspace.cjs");
const base="http://127.0.0.1:3027", api="http://127.0.0.1:8027";
const out=path.resolve(process.argv[2] || ".test_tmp/q6_20261030/tutorial"), dist=path.join(out,"next");
assert(out.startsWith(path.resolve(".test_tmp")+path.sep));
const beforeConfig=fs.readFileSync("tsconfig.json","utf8"),beforeEnv=fs.readFileSync("next-env.d.ts","utf8");
const children=[],checks=[],errors=[],writes=[];
let browser,page,failed;
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function start(exe,args,name,env={}) {
  const log=fs.openSync(path.join(out,name+".log"),"w");
  const child=spawn(exe,args,{cwd:process.cwd(),windowsHide:true,env:{...process.env,...env},stdio:["ignore",log,log]});
  children.push(child);
}
async function ready(url) {
  for(let i=0;i<150;i++){try{if((await fetch(url)).ok)return;}catch{}await pause(500);}
  throw Error("No arrancó el servidor aislado");
}
async function free(port) {
  const server=net.createServer();
  await new Promise((resolve,reject)=>{server.once("error",reject);server.listen(port,"127.0.0.1",()=>server.close(resolve));});
}
async function check(name,action){await action();checks.push({name,passed:true});console.log("PASS "+name);}
const dialog=()=>page.getByRole("dialog",{name:"Tutorial de MEPIA",exact:true});
async function step(index){
  await page.locator('[data-mepia-tour-step="'+index+'"]').waitFor();
  await dialog().waitFor();
  assert.equal(await dialog().count(),1);
  assert.equal(await page.locator(".driver-overlay").count(),1);
}
async function closeTour(){
  await page.getByRole("button",{name:"Cerrar tutorial",exact:true}).click();
  await dialog().waitFor({state:"hidden"});
  assert.equal(await page.locator(".driver-overlay").count(),0);
}
async function login(who){
  await page.getByLabel("Correo",{exact:true}).fill(who+"@example.invalid");
  await page.getByLabel("Contraseña",{exact:true}).fill("synthetic-test-password");
  await page.getByRole("button",{name:"Iniciar sesión",exact:true}).click();
  await page.getByText("Sesión iniciada",{exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelector("#mepia-business")?.value);
}
async function dashboardAnchor(expected) {
  await page.locator(`[data-tour="${expected}"].driver-active-element`).waitFor();
  await dialog().locator(".driver-popover-arrow:not(.driver-popover-arrow-none)").waitFor();
}
async function walk({mobile=false,reload=false}={}){
  const routes=new Set(),sections=new Set();let count=0,reloaded=false;
  for(let index=0;index<26;index++){
    await step(index);count++;
    routes.add(new URL(page.url()).pathname);
    const tabs=page.locator('[data-tour="advanced-config-tabs"]'); const section=await tabs.count()?await tabs.getAttribute("data-seccion"):null;
    if(new URL(page.url()).pathname==="/onboarding" && section) sections.add(Number(section));
    if(index===4 && reload){
      await page.reload();await step(index);reloaded=true;
    }
    const dashboardTarget = {9:"historial",10:"estado",11:"kpis",12:"hallazgos",13:"tendencias"}[index];
    if(dashboardTarget) await dashboardAnchor(dashboardTarget);
    if(new URL(page.url()).pathname==="/onboarding" && index>=20 && index<=23){
      const expected={20:"advanced-config-brand",21:"advanced-config-thresholds",22:"advanced-config-costs",23:"advanced-config-rules"}[index];
      assert.equal(await page.locator(".driver-active-element").getAttribute("data-tour"),expected);
    }
    if(mobile){
      const box=await dialog().boundingBox();assert(box);
      assert(box.x>=-1&&box.x+box.width<=391,"El globo debe caber en móvil");
      assert(box.y>=-1&&box.y+box.height<=845,"El globo debe caber verticalmente");
      if(index===1)await page.screenshot({path:path.join(out,"tutorial_mobile.png"),fullPage:false});
    } else if(index===10) await page.screenshot({path:path.join(out,"tutorial_desktop.png"),fullPage:false});
    await page.getByRole("button",{name:index===25?"Terminar tutorial":"Siguiente paso",exact:true}).click();
  }
  await dialog().waitFor({state:"hidden"});
  assert.equal(await page.locator(".driver-overlay").count(),0);
  assert.deepEqual([...routes].sort(),["/chat","/dashboard","/onboarding","/reportes","/salud","/upload"]);
  assert.deepEqual([...sections].sort(),[1,2,3,4]);
  if(reload)assert(reloaded);
  return count;
}
(async()=>{
  fs.mkdirSync(out,{recursive:true});assert(process.env.MEPIA_TEST_PYTHON);
  await free(3027);await free(8027);
  start(process.env.MEPIA_TEST_PYTHON,["-B","-m","uvicorn","tests.tutorial_server:app","--host","127.0.0.1","--port","8027","--no-access-log"],"api");
  await ready(api+"/__demo__/state");
  const state=await(await fetch(api+"/__demo__/state")).json();
  const sa=await(await fetch(api+"/__test__/session/a")).json(),sb=await(await fetch(api+"/__test__/session/b")).json();
  const ts=require("typescript"),sandbox={exports:{}};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync("components/onboarding/defaults.ts","utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,sandbox);
  const defaults=sandbox.exports.DEFAULT_ONBOARDING_DATA;
  assert(defaults);
  for(const [bid,session] of [[state.business_a,sa],[state.business_empty,sa],[state.business_b,sb]]){
    const response=await fetch(api+"/business/"+bid+"/onboarding",{method:"POST",headers:{Authorization:"Bearer "+session.access_token,"Content-Type":"application/json"},body:JSON.stringify(defaults)});
    assert.equal(response.status,201,"Preparación de ajustes ficticios");
  }
  start(process.execPath,["node_modules/next/dist/bin/next","dev","--hostname","127.0.0.1","--port","3027"],"next",{
    NEXT_TELEMETRY_DISABLED:"1",NEXT_PUBLIC_SUPABASE_URL:api,NEXT_PUBLIC_SUPABASE_ANON_KEY:"synthetic-public-key",AGENTS_API_URL:api,MEPIA_NEXT_DIST_DIR:path.relative(process.cwd(),dist)});
  await ready(base+"/login");
  browser=await chromium.launch({headless:true,channel:process.env.MEPIA_TEST_BROWSER||"msedge"});
  const context=await browser.newContext({viewport:{width:1360,height:1000},reducedMotion:"reduce"});context.setDefaultTimeout(60000);
  await context.route("**/*",route=>[base,api].some(origin=>route.request().url().startsWith(origin+"/"))?route.continue():route.abort());
  page=await context.newPage();page.on("pageerror",e=>errors.push(e.message));
  page.on("request",request=>{if(request.url().startsWith(base+"/api/")&&!["GET","HEAD","OPTIONS"].includes(request.method()))writes.push({path:new URL(request.url()).pathname,method:request.method()});});
  const key=(user,bid)=>"mepia.tutorial.v1:"+user+":"+bid;
  let selected;
  await check("Primera entrada ofrece tutorial y cerrar retira el overlay",async()=>{
    await page.goto(base+"/login");await login("a");await step(0);await closeTour();
    if(await page.getByLabel("Negocio",{exact:true}).inputValue()!==state.business_a){
      await page.getByLabel("Negocio",{exact:true}).selectOption(state.business_a);
      await step(0);await closeTour();
    }
    selected=state.runs.find(row=>row.business_id===state.business_a&&row.date==="2026-10-14").run_id;
    await page.getByLabel("Análisis guardado",{exact:true}).selectOption(selected);
    await page.waitForURL(url=>url.searchParams.get("run_id")===selected);
    await page.waitForFunction(()=>document.querySelectorAll(".kpi-value").length>0);
  });
  await check("Repetir, avanzar y retroceder conserva una sola instancia",async()=>{
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);
    await page.getByRole("button",{name:"Siguiente paso",exact:true}).click();await step(1);
    await page.getByRole("button",{name:"Paso anterior",exact:true}).click();await step(0);
  });
  await check("26 pasos, seis vistas, cuatro secciones y recarga intermedia",async()=>{assert.equal(await walk({reload:true}),26);});
  await check("La corrida elegida y cero válido sobreviven al recorrido",async()=>{
    assert.equal(new URL(page.url()).searchParams.get("run_id"),selected);
    assert.equal(await page.getByLabel("Análisis guardado",{exact:true}).inputValue(),selected);
    await page.waitForFunction(()=>[...document.querySelectorAll(".kpi-value")].some(el=>/^0\s*MXN$/.test(el.textContent.trim())));
  });
  await check("Terminar persiste la preferencia y no reinicia al recargar",async()=>{
    assert.deepEqual(await page.evaluate(k=>JSON.parse(localStorage.getItem(k)),key(sa.user.id,state.business_a)),{visto:true});
    await page.reload();await page.getByRole("button",{name:"Ver tutorial",exact:true}).waitFor();
    assert.equal(await dialog().count(),0);
  });
  await check("Un enlace explícito se respeta aunque no se haya visto el tutorial",async()=>{
    await page.evaluate(k=>localStorage.removeItem(k),key(sa.user.id,state.business_a));
    await page.goto(base+"/dashboard?run_id="+selected);
    await page.getByLabel("Análisis guardado",{exact:true}).waitFor();await pause(300);
    assert.equal(new URL(page.url()).searchParams.get("run_id"),selected);assert.equal(await dialog().count(),0);
  });
  await check("Escape cierra, devuelve el foco y permite repetir",async()=>{
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);
    await page.keyboard.press("Escape");await dialog().waitFor({state:"hidden"});
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).waitFor();
    assert.equal(await page.getByRole("button",{name:"Ver tutorial",exact:true}).evaluate(el=>el===document.activeElement),true);
  });
  await check("Cambiar a negocio vacío separa el progreso y limpia los resultados",async()=>{
    await page.evaluate(k=>localStorage.removeItem(k),key(sa.user.id,state.business_empty));
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);
    await page.getByRole("button",{name:"Siguiente paso",exact:true}).click();await step(1);
    await page.getByLabel("Negocio",{exact:true}).selectOption(state.business_empty);
    await page.waitForURL(url=>!url.searchParams.has("run_id"));await step(0);
    assert.equal(await page.locator(".kpi-value").count(),0);assert.equal(await page.locator(".driver-overlay").count(),1);
    assert.equal(await page.evaluate(k=>JSON.parse(localStorage.getItem(k)).paso,key(sa.user.id,state.business_empty)),0);
    assert.equal(await page.evaluate(k=>JSON.parse(localStorage.getItem(k)).paso,key(sa.user.id,state.business_a)),1);
    await closeTour();
    await page.evaluate(k=>localStorage.setItem(k,JSON.stringify({paso:9})),key(sa.user.id,state.business_empty));
    await page.reload();
    for(const [index,target] of [[9,"historial"],[10,"estado"],[11,"estado"],[12,"estado"],[13,"estado"]]){
      await step(index);
      await dashboardAnchor(target);
      if(index<13) await page.getByRole("button",{name:"Siguiente paso",exact:true}).click();
    }
    assert.match(await dialog().innerText(),/elige|elegir/i);
    await closeTour();
    await page.getByLabel("Negocio",{exact:true}).selectOption(state.business_a);await step(1);
    await closeTour();
  });
  await check("Salir con el tutorial abierto limpia la interfaz y otra cuenta tiene su recorrido",async()=>{
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);
    await page.getByRole("button",{name:"Cerrar sesión",exact:true}).evaluate(el=>el.click());
    await page.waitForURL(url=>url.pathname==="/login");assert.equal(await page.locator(".driver-overlay").count(),0);
    await login("b");await step(0);
    assert.equal(await page.getByLabel("Negocio",{exact:true}).inputValue(),state.business_b);await closeTour();
  });
  await check("Móvil: 26 pasos, menú accesible y globos dentro de 390x844",async()=>{
    await page.setViewportSize({width:390,height:844});
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);
    assert.equal(await walk({mobile:true}),26);
  });
  await check("Progreso inválido no rompe la entrada ni la repetición",async()=>{
    await page.evaluate(k=>localStorage.setItem(k,JSON.stringify({paso:999})),key(sb.user.id,state.business_b));
    await page.goto(base+"/dashboard");await step(0);await closeTour();
    await page.getByRole("button",{name:"Ver tutorial",exact:true}).click();await step(0);await closeTour();
  });
  await check("El recorrido no envía análisis, preguntas, archivos ni ajustes",async()=>{
    assert.deepEqual(writes,[]);const final=await(await fetch(api+"/__demo__/state")).json();
    assert.equal(final.real_provider_calls,0);assert.equal(final.analyses_created,0);assert.deepEqual(errors,[]);
  });
})().catch(async error=>{failed=error;console.error(error.stack);if(page)await page.screenshot({path:path.join(out,"failure.png"),fullPage:true}).catch(()=>{});process.exitCode=1;})
.finally(async()=>{
  if(browser)await browser.close();
  for(const child of children){
    if(!child.pid||child.exitCode!==null)continue;
    if(process.platform==="win32")await new Promise(resolve=>{const killer=spawn("taskkill.exe",["/pid",String(child.pid),"/t","/f"],{windowsHide:true,stdio:"ignore"});killer.once("exit",resolve);});
    else child.kill();
  }
  restoreGeneratedTypes({root:process.cwd(),distDir:dist,tsconfigBefore:beforeConfig,nextEnvBefore:beforeEnv});
  fs.writeFileSync(path.join(out,"report.json"),JSON.stringify({passed:!failed,checks,errors,writes,error:failed?.message,real_provider_calls:0},null,2));
});
