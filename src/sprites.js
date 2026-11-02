// Four cheer sprites in the Shift & Play style: chunky black shapes, the #RUNTOMTL pink, round dots from the logo.
// Keys stay the emoji that the database stores, so nothing changes server-side.
const SPRITES = {
  "🔥": `<svg viewBox="0 0 64 64" class="spr spr-fire" aria-label="Fire"><g class="b"><path class="o" d="M32 5c7 11 18 18 18 33 0 12-8 20-18 20s-18-8-18-20c0-8 5-12 8-20 3 6 5 8 8 8 0-8 0-14 2-21z"/><path class="i" d="M32 30c4 6 9 9 9 15 0 6-4 10-9 10s-9-4-9-10c0-4 3-6 5-10 2 3 3 3 4 3 0-3 0-5 0-8z"/></g></svg>`,
  "💪": `<svg viewBox="0 0 64 64" class="spr spr-bolt" aria-label="Strong"><g class="b"><path class="o" d="M37 4 12 36h16l-5 24 29-34H35l6-22z"/><path class="i" d="M34 13 21 31h11l-3 15 14-17H32z"/></g></svg>`,
  "❤️": `<svg viewBox="0 0 64 64" class="spr spr-heart" aria-label="Love"><g class="b"><path class="o" d="M32 57S7 42 7 24C7 15 13 9 21 9c5 0 9 3 11 7 2-4 6-7 11-7 8 0 14 6 14 15 0 18-25 33-25 33z"/><path class="i" d="M32 48S15 37 15 25c0-5 3-8 7-8 4 0 7 3 10 8 3-5 6-8 10-8 4 0 7 3 7 8 0 12-17 23-17 23z"/></g></svg>`,
  "🏃": `<svg viewBox="0 6 64 64" class="spr spr-run" aria-label="Run"><g class="spd"><path class="i st2" d="M2 30h9M4 38h7M2 46h8"/></g><g class="b"><path class="o" d="M14 44c0-13 3-20 9-21l7-1c1 5 5 8 10 8l9 3c6 2 10 5 10 9v2H14z"/><path class="i" d="M12 46h48c0 5-3 8-8 8H19c-4 0-7-3-7-8z"/><circle cx="30" cy="31" r="2.6" fill="var(--card,#fff)"/><circle cx="36" cy="34" r="2.6" fill="var(--card,#fff)"/><circle cx="42" cy="36" r="2.6" fill="var(--card,#fff)"/></g></svg>`
};
const SPRITE_CSS = `
.spr{width:100%;height:100%;display:block;overflow:visible}
.spr .o{fill:var(--sprite-ink,currentColor)} .spr .i{fill:var(--accent)}
.spr .st{fill:none;stroke:var(--sprite-ink,currentColor);stroke-width:7;stroke-linecap:round;stroke-linejoin:round}
.spr .st2{fill:none;stroke:var(--accent);stroke-width:3.5;stroke-linecap:round}
.spr .b{transform-origin:32px 58px}
/* idle: alive but quiet */
.spr-fire .b{animation:sp-flick 1.6s ease-in-out infinite}
.spr-fire .i{transform-origin:32px 55px;animation:sp-sway 1.1s ease-in-out infinite}
.spr-heart .b{transform-origin:32px 34px;animation:sp-beat 2.4s ease-in-out infinite}
.spr-bolt .b{transform-origin:32px 32px;animation:sp-zap 3.2s ease-in-out infinite}
.spr-run .b{transform-origin:58px 54px;animation:sp-step .8s ease-in-out infinite}
.spr-run .spd{animation:sp-speed .8s linear infinite}
@keyframes sp-flick{0%,100%{transform:scale(1,1)}30%{transform:scale(.96,1.05)}60%{transform:scale(1.03,.97)}}
@keyframes sp-sway{0%,100%{transform:skewX(0) scaleY(1)}50%{transform:skewX(-6deg) scaleY(1.08)}}
@keyframes sp-beat{0%,40%,100%{transform:scale(1)}10%{transform:scale(1.12)}20%{transform:scale(.97)}30%{transform:scale(1.07)}}
@keyframes sp-zap{0%,82%,100%{transform:rotate(0) scale(1)}86%{transform:rotate(-8deg) scale(1.1)}90%{transform:rotate(6deg) scale(1.05)}94%{transform:rotate(-3deg) scale(1.08)}}
@keyframes sp-step{0%,100%{transform:rotate(0) translateY(0)}35%{transform:rotate(-14deg) translateY(-3px)}60%{transform:rotate(-4deg) translateY(-1px)}}
@keyframes sp-legA{0%,100%{transform:rotate(-22deg)}50%{transform:rotate(22deg)}}
@keyframes sp-legB{0%,100%{transform:rotate(22deg)}50%{transform:rotate(-22deg)}}
@keyframes sp-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
@keyframes sp-speed{0%{transform:translateX(4px);opacity:0}30%{opacity:1}100%{transform:translateX(-8px);opacity:0}}
/* tapped: a big pop and a burst of the logo dots */
.pop .b{animation:sp-pop .55s cubic-bezier(.2,1.6,.4,1) both!important}
@keyframes sp-pop{0%{transform:scale(1)}35%{transform:scale(1.35) rotate(-6deg)}100%{transform:scale(1)}}
.burst{position:absolute;left:50%;top:50%;width:0;height:0;pointer-events:none}
.burst i{position:absolute;left:-5px;top:-5px;width:10px;height:10px;border-radius:50%;background:var(--accent);animation:sp-dot .7s ease-out forwards}
@keyframes sp-dot{0%{transform:translate(0,0) scale(1);opacity:1}100%{transform:translate(var(--dx),var(--dy)) scale(.3);opacity:0}}
@media (prefers-reduced-motion:reduce){ .spr *,.spr .b{animation:none!important} .burst{display:none} }
`;
function spriteBurst(el){ const b=document.createElement("span"); b.className="burst"; const n=7;
  for(let k=0;k<n;k++){ const a=-Math.PI/2+(k-(n-1)/2)*0.42, d=46+k%2*12; const s=document.createElement("i"); s.style.setProperty("--dx",(Math.cos(a)*d).toFixed(0)+"px"); s.style.setProperty("--dy",(Math.sin(a)*d).toFixed(0)+"px"); s.style.width=s.style.height=(12-Math.abs(k-3)*2)+"px"; b.appendChild(s); }
  el.appendChild(b); el.classList.remove("pop"); void el.offsetWidth; el.classList.add("pop"); setTimeout(()=>{ b.remove(); el.classList.remove("pop"); },750); }
