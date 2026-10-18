/* Site behaviour: search overlay (searches the catalog in the browser), product gallery and option picker. */
(function(){
  "use strict";
  var ROUTE=window.ROUTE||{};
  function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
  function money(v){return "$"+Number(v).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});}
  function slug(s){return s?s.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,""):"national";}
  var BASE=(function(){var p=location.pathname.replace(/index\.html$/,"");var parts=p.split("/");if(parts[parts.length-1]==="")parts.pop();for(var i=0;i<(ROUTE.depth||0);i++)parts.pop();return parts.join("/")+"/";})();
  window.SITE_BASE=BASE;
  function pathFor(p){return BASE+slug(p.state)+"/"+p.exam+"/"+p.slug+"/";}

  /* footer year */
  document.querySelectorAll("[data-year]").forEach(function(e){e.textContent=new Date().getFullYear();});

  /* ---------- search ---------- */
  var ov=document.createElement("div"); ov.className="srch"; ov.hidden=true;
  ov.innerHTML='<div class="srch-back" data-sclose></div><div class="srch-box" role="dialog" aria-modal="true" aria-label="Search">'+
    '<form class="srch-form" role="search" action="'+esc(BASE)+'search/" method="get"><label class="sr-only" for="srchQ">Search</label><input class="srch-q" id="srchQ" name="q" type="search" placeholder="State, exam or product" autocomplete="off"><button type="button" class="srch-x" data-sclose aria-label="Close search">&times;</button></form>'+
    '<div class="srch-res" aria-live="polite"></div><p class="srch-hint">Try "Florida commercial", "master electrical" or "highlighted". Press Esc to close.</p></div>';
  document.body.appendChild(ov);
  var q=ov.querySelector(".srch-q"), res=ov.querySelector(".srch-res"), opener=null;
  function ensureCatalog(cb){
    if(window.CATALOG){cb();return;}
    var s=document.createElement("script"); s.src=BASE+"shared/catalog.js"; s.onload=cb; document.head.appendChild(s);
  }
  function words(s){return s.toLowerCase().replace(/[^a-z0-9 ]/g," ").split(/\s+/).filter(function(w){return w&&["nascla","exam","prep","the","for"].indexOf(w)<0;});}
  function find(text){
    var t=words(text); if(!t.length) return [];
    return (window.CATALOG||[]).map(function(p){
      var hay=(p.title+" "+(p.state||"nationwide")+" "+p.examName+" "+p.kindName).toLowerCase(), sc=0, all=true;
      t.forEach(function(w){ if(hay.indexOf(w)>-1){sc+=1; if((p.state||"").toLowerCase().indexOf(w)===0)sc+=3; if(p.examName.toLowerCase().indexOf(w)>-1)sc+=1;} else all=false; });
      return {p:p,sc:all?sc+10:sc};
    }).filter(function(x){return x.sc>0;}).sort(function(a,b){return b.sc-a.sc||b.p.rank-a.p.rank;}).slice(0,12).map(function(x){return x.p;});
  }
  function rowHtml(p){return '<a class="srch-row" href="'+esc(pathFor(p))+'"><img src="'+esc(p.image)+'" alt="" loading="lazy"><span>'+esc(p.kindName)+'<small>'+esc((p.state||"Nationwide")+" · "+p.examName)+'</small></span><b>'+money(p.price)+'</b></a>';}
  function render(target,text){
    var hits=find(text);
    target.innerHTML=hits.length?hits.map(rowHtml).join(""):(text.trim()?'<p class="srch-hint">Nothing matched. Try a state name or an exam.</p>':"");
  }
  function openS(){opener=document.activeElement; ov.hidden=false; document.body.style.overflow="hidden"; ensureCatalog(function(){render(res,q.value);}); setTimeout(function(){q.focus();},20);}
  function closeS(){ov.hidden=true; document.body.style.overflow=""; if(opener&&opener.focus)opener.focus();}
  document.addEventListener("click",function(e){ if(e.target.closest("[data-sopen]")){e.preventDefault();openS();} else if(e.target.closest("[data-sclose]")) closeS(); });
  document.addEventListener("keydown",function(e){
    if(e.key==="Escape"&&!ov.hidden) closeS();
    if(e.key==="/"&&ov.hidden&&!/input|textarea|select/i.test((document.activeElement||{}).tagName||"")){e.preventDefault();openS();}
  });
  q.addEventListener("input",function(){ensureCatalog(function(){render(res,q.value);});});
  var page=document.getElementById("searchPage");
  if(page){
    var pq=page.querySelector(".srch-q"), out=document.getElementById("searchOut"), init=new URLSearchParams(location.search).get("q")||"";
    pq.value=init; ensureCatalog(function(){render(out,init);});
    pq.addEventListener("input",function(){render(out,pq.value);});
    page.addEventListener("submit",function(e){e.preventDefault();render(out,pq.value);});
  }

  /* ---------- product page ---------- */
  var P=window.PRODUCT;
  if(P){
    var main=document.querySelector(".gallery .main img");
    document.querySelectorAll(".thumbs button").forEach(function(b){b.addEventListener("click",function(){
      main.src=b.getAttribute("data-src"); document.querySelectorAll(".thumbs button").forEach(function(x){x.classList.remove("on");}); b.classList.add("on");});});
    var buys=document.querySelectorAll("[data-buy]"), now=document.querySelectorAll("[data-now]"), was=document.getElementById("pWas"), save=document.getElementById("pSave");
    document.querySelectorAll('input[name="v"]').forEach(function(r){r.addEventListener("change",function(){
      var v=P.variants.filter(function(x){return String(x.id)===r.value;})[0]; if(!v) return;
      buys.forEach(function(a){a.href="https://1examprep.com/cart/"+v.id+":1";});
      now.forEach(function(n){n.textContent=money(v.price);});
      var c=Number(v.compareAt||0), n=Number(v.price);
      if(was&&save){ if(c>n){was.hidden=false;save.hidden=false;was.textContent=money(c);save.textContent="Save "+Math.round((c-n)/c*100)+"%";} else {was.hidden=true;save.hidden=true;} }
    });});
    if(document.querySelector(".stickybar")) document.body.classList.add("has-sticky");
  }
})();
