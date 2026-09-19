import { HtmlValidate } from 'html-validate';
import { readdir, readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'docs/qa/ci');
await mkdir(out,{recursive:true});
async function collect(dir) {
  const result=[];
  for (const entry of await readdir(dir,{withFileTypes:true})) {
    if (['docs','content','qa','node_modules','.git','.github'].includes(entry.name)) continue;
    const file=path.join(dir,entry.name);
    if(entry.isDirectory()) result.push(...await collect(file));
    else if(entry.name.endsWith('.html')) result.push(file);
  }
  return result;
}
const validator=new HtmlValidate({extends:['html-validate:standard','html-validate:a11y']});
const results=[];
const files=await collect(root);
for (const file of files) {
  const report=await validator.validateString(await readFile(file,'utf8'),file);
  if(!report.valid) results.push(...report.results);
}
const summary={files:files.length,errors:results.reduce((n,r)=>n+r.errorCount,0),warnings:results.reduce((n,r)=>n+r.warningCount,0),results};
await writeFile(path.join(out,'html-after.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({files:summary.files,errors:summary.errors,warnings:summary.warnings}));
if(summary.errors) process.exitCode=1;
