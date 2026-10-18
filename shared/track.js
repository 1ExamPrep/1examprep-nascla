/* Click and conversion tracking. Sends events to Google Analytics 4 (gtag) and, if present, Google Tag Manager's
   dataLayer and the Meta Pixel. Does nothing if no analytics ID is configured. Edit site-config.json, not this file.

   Events sent (GA4 names, with standard ecommerce fields where they exist):
     view_item         product page opened                      items[]
     select_item       "What's inside" / product card clicked   items[]
     begin_checkout    any Buy now button                       items[], value, currency, button_location
     search            site search used                         search_term
     filter_change     state / level changed                    state, level, year
     phone_click       phone number tapped                      phone
     outbound_click    link to 1examprep.com (non-checkout)     link_url
*/
(function(){
  "use strict";
  var C=window.CATALOG||[], P=window.PRODUCT||null;
  function send(name,params){
    params=params||{};
    try{ if(window.dash&&window.dash.track&&name!=="page_view") dash.track(name,params); }catch(e){}
    try{ if(window.gtag) gtag("event",name,params); }catch(e){}
    try{ window.dataLayer=window.dataLayer||[]; if(!window.gtag) dataLayer.push(Object.assign({event:name},params)); }catch(e){}
    try{ if(window.fbq){ var map={begin_checkout:"InitiateCheckout",view_item:"ViewContent",search:"Search",select_item:"ViewContent"}; if(map[name]) fbq("track",map[name],{content_ids:(params.items||[]).map(function(i){return i.item_id;}),content_name:(params.items||[{}])[0].item_name,value:params.value,currency:"USD",search_string:params.search_term}); } }catch(e){}
  }
  function item(p,variantId){
    if(!p) return null;
    var v=(p.variants||[]).filter(function(x){return String(x.id)===String(variantId);})[0]||(p.variants||[])[0]||{};
    return {item_id:String(p.id),item_name:p.tierName?((p.state||"General")+" "+p.level+" "+p.tierName):(p.title||""),item_variant:v.title||"",price:Number(v.price||p.price||0),quantity:1,
            item_category:p.level||"",item_category2:p.state||"General",item_category3:p.tierName||"",item_brand:(window.SITE||{}).brand||""};
  }
  function flat(p,it){ return p?{product_id:String(p.id),state:p.state||"General",level:p.level||"",tier:p.tierName||"",price:it?it.price:Number(p.price||0),title:it?it.item_name:(p.title||"")}:{}; }
  function byId(id){ if(P&&String(P.id)===String(id)) return P; return C.filter(function(x){return String(x.id)===String(id);})[0]||null; }
  function productFor(el){
    var card=el.closest("[data-id]"); if(card) return byId(card.getAttribute("data-id"));
    if(P) return P; return null;
  }
  function variantFromHref(h){ var m=(h||"").match(/\/cart\/(\d+):/); return m?m[1]:null; }
  function where(el){
    if(el.closest(".stickybar")) return "sticky_bar";
    if(el.closest("#product-modal")) return "quick_view";
    if(el.closest(".buybox")) return "product_page";
    if(el.closest(".nav")) return "header";
    if(el.closest("#rail")) return "package_card";
    if(el.closest("#singlesGrid")) return "singles_card";
    if(el.closest(".final")) return "bottom_cta";
    return "other";
  }

  document.addEventListener("click",function(e){
    var a=e.target.closest("a,button"); if(!a) return;
    var href=a.getAttribute("href")||"";
    if(/\/cart\/\d+:/.test(href)){
      var p=productFor(a), vid=variantFromHref(href), it=item(p,vid);
      send("begin_checkout",{currency:"USD",value:it?it.price:undefined,items:it?[it]:[],button_location:where(a),variant_id:vid});
      send("buy_now_click",Object.assign(flat(p,it),{variant_id:vid,button_location:where(a)}));
      return;
    }
    if(a.hasAttribute("data-details")||a.classList.contains("rel")){
      var p2=productFor(a)||byId((a.getAttribute("href")||"").split("/").filter(Boolean).slice(-1)[0]);
      var it2=item(p2); send("select_item",Object.assign(flat(p2,it2),{items:it2?[it2]:[],item_list_name:where(a),button_location:where(a)})); return;
    }
    if(/^tel:/.test(href)){ send("phone_click",{phone:href.replace("tel:",""),button_location:where(a)}); return; }
    if(/^https?:\/\/(www\.)?1examprep\.com/.test(href)){ send("outbound_click",{link_url:href,button_location:where(a)}); return; }
    if(a.hasAttribute("data-sopen")){ send("search_open",{}); return; }
    if(a.closest(".srch-row")){ send("search_result_click",{link_url:a.getAttribute("href"),search_term:(document.querySelector(".srch-q")||{}).value||""}); return; }
    if(a.hasAttribute("data-level")){ send("filter_change",{level:a.getAttribute("data-level"),state:(document.querySelector(".spick-val")||{}).textContent||""}); return; }
    if(a.hasAttribute("data-v")&&a.closest(".spick-list")){ send("filter_change",{state:a.getAttribute("data-v"),level:(document.querySelector('[data-level][aria-pressed="true"]')||{}).getAttribute?((document.querySelector('[data-level][aria-pressed="true"]')||{}).getAttribute("data-level")):""}); return; }
    if(a.closest(".railnav")){ send("package_swipe",{direction:a.getAttribute("data-dir")}); return; }
  },true);

  /* search terms (debounced) */
  var t; document.addEventListener("input",function(e){ if(!e.target.classList||!e.target.classList.contains("srch-q")) return; clearTimeout(t); var v=e.target.value; t=setTimeout(function(){ if(v.trim().length>=3) send("search",{search_term:v.trim()}); },900); },true);

  /* variant choice on product page */
  document.addEventListener("change",function(e){ if(e.target.name==="v"&&P){ var it=item(P,e.target.value); send("select_variant",Object.assign(flat(P,it),{items:it?[it]:[],variant_id:e.target.value})); } },true);

  /* product page view */
  if(P){ var it0=item(P); send("view_item",Object.assign(flat(P,it0),{currency:"USD",value:it0?it0.price:undefined,items:it0?[it0]:[]})); }

  /* FAQ opens */
  document.addEventListener("toggle",function(e){ var d=e.target; if(d.tagName==="DETAILS"&&d.open&&d.closest(".faq")){ send("faq_open",{question:(d.querySelector("summary")||{}).textContent||""}); } },true);
})();
