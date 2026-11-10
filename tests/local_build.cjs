const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const {restoreGeneratedTypes}=require('./chat_step5_workspace.cjs');
const root=process.cwd(),out=path.resolve(process.argv[2]),distDir=path.join(out,'next');
if(!out.startsWith(path.resolve('.test_tmp')+path.sep))throw Error('Salida de build fuera de .test_tmp');
fs.mkdirSync(out,{recursive:true});
const tsconfigBefore=fs.readFileSync('tsconfig.json','utf8'),nextEnvBefore=fs.readFileSync('next-env.d.ts','utf8');
let result;
try {
 result=spawnSync(process.execPath,['node_modules/next/dist/bin/next','build'],{cwd:root,windowsHide:true,encoding:'utf8',maxBuffer:3000000,
  env:{...process.env,NEXT_TELEMETRY_DISABLED:'1',MEPIA_NEXT_DIST_DIR:path.relative(root,distDir)}});
 fs.writeFileSync(path.join(out,'build.log'),(result.stdout||'')+(result.stderr||''));
}finally{restoreGeneratedTypes({root,distDir,tsconfigBefore,nextEnvBefore});}
const types=spawnSync(process.execPath,['node_modules/typescript/bin/tsc','--noEmit','--incremental','false'],{cwd:root,windowsHide:true,encoding:'utf8'});
fs.writeFileSync(path.join(out,'types.log'),(types.stdout||'')+(types.stderr||''));
const report={build:result.status,types:types.status,config_restored:fs.readFileSync('tsconfig.json','utf8')===tsconfigBefore,next_env_restored:fs.readFileSync('next-env.d.ts','utf8')===nextEnvBefore,public_backend_origin:process.env.NEXT_PUBLIC_SUPABASE_URL};
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
process.exitCode=report.build===0&&report.types===0&&report.config_restored&&report.next_env_restored?0:1;
