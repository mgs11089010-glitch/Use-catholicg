
window.__setV=(el,v)=>{const p=el.tagName=='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(p,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));};
window.__fill3d=async(slug)=>{
 const B='https://use-catholicg.vercel.app/shopee/';
 const D=(await (await fetch(B+'listings3d.json?'+Date.now())).json())[slug];
 const dt=new DataTransfer();
 for(const n of D.imgs){const b=await (await fetch(B+n)).blob();dt.items.add(new File([b],n,{type:'image/jpeg'}));}
 const fi=[...document.querySelectorAll('input[type=file]')].find(i=>i.multiple)||document.querySelectorAll('input[type=file]')[0];
 fi.files=dt.files;fi.dispatchEvent(new Event('change',{bubbles:true}));
 const t=[...document.querySelectorAll('input')].find(i=>(i.placeholder||'').startsWith('Nome da marca'));
 window.__setV(t,D.titulo);
 const ql=document.querySelector('.ql-editor');const q=ql.parentElement.__quill||ql.closest('.ql-container')?.__quill;q.setText(D.desc);
 const lab=[...document.querySelectorAll('*')].filter(e=>e.children.length==0&&e.textContent.trim()=='SKU principal')[0];
 const sk=lab.closest('[class*=form-item],[class*=item]').querySelector('input');window.__setV(sk,D.sku);
 await new Promise(r=>setTimeout(r,1500));
 const L=[...document.querySelectorAll('input:not([type=file]),textarea')];
 const st=L.findIndex(i=>i.placeholder=='SKU da Variação')+1;
 D.prices.forEach((p,k)=>{window.__setV(L[st+5*k],p);window.__setV(L[st+5*k+1],'30');});
 await new Promise(r=>setTimeout(r,600));
 const L2=[...document.querySelectorAll('input:not([type=file]),textarea')];
 return {title:t.value.length, desc:document.body.innerText.match(/\d+\/5000/g), sku:sk.value, vars:D.prices.map((p,k)=>L2[st+5*k].value+'/'+L2[st+5*k+1].value), opts:L2.filter(i=>i.placeholder=='Inserir'&&i.tagName=='INPUT').map(i=>i.value).filter(Boolean), imgs:document.body.innerText.match(/Adicionar Imagem \(\d\/9\)/g)};
};
window.__save3d=()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()=='Salvar e Não Publicar');b.click();return !!b};
