let kind='image', busy=false, lastSnapshot='';
const $=id=>document.getElementById(id);
const labels={queued:'Đang chờ',running:'Đang thực hiện',succeeded:'Hoàn tất',failed:'Không thành công',download_failed:'Đã tạo trên Flow · chưa tải về',interrupted:'Bị gián đoạn',indeterminate:'Cần kiểm tra trên Flow'};
async function api(path, data){
  const response=await fetch(path, data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});
  const value=await response.json();
  if(!response.ok) throw new Error(value.error||'Không kết nối được ứng dụng.');
  return value;
}
document.querySelectorAll('[data-kind]').forEach(button=>button.addEventListener('click',()=>{
  kind=button.dataset.kind;
  document.querySelectorAll('[data-kind]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',b===button?'true':'false');});
  $('model').disabled=kind==='video';
  $('aspect').replaceChildren(...(kind==='image'?['16:9','9:16','1:1','4:3','3:4']:['16:9','9:16']).map(text=>new Option(text,text)));
  $('credit-label').hidden=kind!=='video'; $('credits').required=kind==='video';
  $('submit').textContent=kind==='image'?'✦  Tạo ảnh':'▷  Tạo video';
}));
$('prompt').addEventListener('input',()=>{$('counter').textContent=`${$('prompt').value.length} / 5000`;});
async function send(data){
  if(busy)return;
  busy=true; $('error').textContent='';
  document.querySelectorAll('#submit,#login,#status').forEach(b=>b.disabled=true);
  try{await api('/api/jobs',{...data,profile:$('profile').value,background:$('background').checked}); await refresh(); $('history').scrollIntoView({behavior:'smooth'});}
  catch(error){$('error').textContent=error.message;}
  finally{busy=false;document.querySelectorAll('#submit,#login,#status').forEach(b=>b.disabled=false);}
}
$('generate').addEventListener('submit',event=>{event.preventDefault();send({action:'generate',kind,prompt:$('prompt').value,aspect:$('aspect').value,model:$('model').value,confirm_video:$('credits').checked});});
$('login').addEventListener('click',()=>send({action:'login'}));
$('status').addEventListener('click',()=>send({action:'status'}));
$('recover-form').addEventListener('submit',event=>{event.preventDefault();send({action:'download',kind:'video',media_id:$('media-id').value.trim()});});
try{$('background').checked=localStorage.getItem('gflow-minimize')!=='false';}catch{}
$('background').addEventListener('change',()=>{try{localStorage.setItem('gflow-minimize',String($('background').checked));}catch{}});
function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function render(jobs){
  $('job-count').textContent=`${jobs.length} tác vụ`;
  if(!jobs.length)return;
  $('jobs').replaceChildren(...jobs.map(job=>{
    const card=node('article',undefined,'job'), head=node('div',undefined,'job-head');
    head.append(node('p',job.action==='login'?'Đăng nhập Google':job.action==='status'?'Kiểm tra phiên':job.action==='download'?'Tải lại video đã tạo'+(job.prompt?' · '+job.prompt:''):job.prompt,'job-title'),node('span',labels[job.status]||job.status,`job-status ${job.status}`));
    card.append(head,node('small',new Date(job.created*1000).toLocaleString('vi-VN')));
    const gallery=node('div',undefined,'gallery');
    job.files.forEach(file=>{const box=node('div'),url='/out/'+file.split('/').map(encodeURIComponent).join('/'),media=node(file.endsWith('.mp4')?'video':'img');media.src=url;if(media.tagName==='VIDEO')media.controls=true;else{media.alt=job.prompt;media.loading='lazy';}const link=node('a','Tải về');link.href=url;link.download=file.split('/').pop();box.append(media,link);gallery.append(box);});
    card.append(gallery);
    if(job.status==='download_failed' && job.media_id){
      card.append(node('small','Video đã được tạo trên Flow. Chỉ tải lại video này, không tạo mới và không dùng thêm credit.'));
      const retry=node('button','↓ Tải lại video đã tạo');retry.type='button';retry.style.marginTop='12px';
      retry.addEventListener('click',()=>send({action:'recover',source_id:job.id}));card.append(retry);
    }
    if(job.message){const details=node('details'),summary=node('summary','Chi tiết tác vụ');details.append(summary,node('pre',job.message));card.append(details);}
    if(['failed','interrupted','indeterminate'].includes(job.status))card.append(node('small','Không tự động thử lại. Nếu đã gửi yêu cầu tạo, hãy kiểm tra dự án Google Flow trước khi tạo lần nữa.'));
    return card;
  }));
}
async function refresh(){
  try{const [health,jobs]=await Promise.all([api('/api/health'),api('/api/jobs')]);
    $('connection').textContent=`●  Đã kết nối · v${health.version}`;
    $('setup').textContent=!health.display_available?'Giao diện đang hoạt động. Máy chủ hiện chưa có màn hình cho bước đăng nhập Google. Để tạo ảnh/video, hãy chạy ứng dụng trên máy tính có Chrome và đăng nhập một lần.':health.session_saved?'Đã lưu phiên Google. Bạn có thể kiểm tra phiên trước khi tạo nội dung.':'Bắt đầu bằng cách nhấn “Đăng nhập Google”, rồi hoàn tất đăng nhập trong cửa sổ Chrome.';
    $('login').disabled=busy||!health.display_available;
    const serialized=JSON.stringify(jobs);if(serialized!==lastSnapshot){render(jobs);lastSnapshot=serialized;}
  }catch(error){$('connection').textContent='●  Mất kết nối';$('error').textContent=error.message;}
}
refresh();setInterval(refresh,2500);
