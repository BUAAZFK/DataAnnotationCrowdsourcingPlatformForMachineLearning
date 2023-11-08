const canvasMain = document.querySelector('.canvasMain');
const canvas = document.getElementById('canvas');
const resultGroup = document.querySelector('.resultGroup');

// 设置画布宽高背景色
canvas.width = canvas.clientWidth;
canvas.height = canvas.clientHeight;
canvas.style.background = "#8c919c";

const annotate = new LabelImage({
	canvas: canvas,
	scaleCanvas: document.querySelector('.scaleCanvas'),
	scalePanel: document.querySelector('.scalePanel'),
	annotateState: document.querySelector('.annotateState'),
	canvasMain: canvasMain,
	resultGroup: resultGroup,
	crossLine: document.querySelector('.crossLine'),
	labelShower: document.querySelector('.labelShower'),
	screenShot: document.querySelector('.screenShot'),
	screenFull: document.querySelector('.screenFull'),
	colorHex: document.querySelector('#colorHex'),
	toolTagsManager: document.querySelector('.toolTagsManager'),
	historyGroup: document.querySelector('.historyGroup')
});

// 初始化交互操作节点
const prevBtn = document.querySelector('.pagePrev');                    // 上一张
const nextBtn = document.querySelector('.pageNext');                    // 下一张
const taskName = document.querySelector('.pageName');                   // 标注任务名称
const processIndex = document.querySelector('.processIndex');           // 当前标注进度
const processSum = document.querySelector('.processSum');               // 当前标注任务总数
const segBtn = document.getElementById('seg');
const detectBtn = document.getElementById('detect');

var imgIndex = init_data.index_now;
var imgSum =init_data.lenth;
var trueimgIndex;
var projectId=init_data.taskId_ano;
var progress;
var len_of_labeled;
var label_url=init_data.label_url;
var identity = init_data.identity;//"creator\worker
// console.log("yes");
// console.log(init_data);
initImage(imgIndex,imgSum);


// $(document).ready(function(){
// 	$.get("/worker/w1/getlenth", function(ret){
// 		imgIndex = Number(ret.index_now);
// 		imgSum=Number(ret.lenth);
// 		initImage(imgIndex,imgSum);
// 	});
// console.log("yes");
// console.log(init_data);
// {#var button=document.getElementById('submit')#}
$(document).ready(function() {
	$('#submit').click(function() {
		if (identity==="worker") {
			$.ajax({
				url: label_url + '/label',
				type: 'post',
				data: {
					classdata: $('#classlabel').serialize(),
					pid: projectId,
					iid: trueimgIndex,
				},
				success: function (response) {
					// 在这里处理服务器响应
					console.log("seccessfull trans class data!")
				}
			});
			alert("提交成功");
			if (imgIndex >= imgSum) {
			imgIndex = 1;
			selectImage(1);
			}
			else {
				imgIndex++;
				selectImage(imgIndex);
			}
		}else{
			alert("当前身份不允许提交数据");
		}
	});
});


// });
// let imgIndex = 1;       //标定图片默认下标;
// let imgSum = 10;        // 选择图片总数;
// initImage();
// 初始化图片状态
function initImage(imgIndex,imgSum) {
	selectImage(imgIndex);
	processSum.innerText = imgSum;
}

//切换操作选项卡
let tool = document.getElementById('tools');
tool.addEventListener('click', function(e) {
	for (let i=0; i<tool.children.length; i++) {
		tool.children[i].classList.remove('focus');
	}
	e.target.classList.add('focus');
	switch(true) {
		case e.target.className.indexOf('toolDrag') > -1:  // 拖拽
			annotate.SetFeatures('dragOn', true);
			break;
		case e.target.className.indexOf('toolRect') > -1:  // 矩形
			annotate.SetFeatures('rectOn', true);
			break;
		case e.target.className.indexOf('toolPolygon') > -1:  // 多边形
			annotate.SetFeatures('polygonOn', true);
			break;
		case e.target.className.indexOf('toolTagsManager') > -1:  // 标签管理工具
			annotate.SetFeatures('tagsOn', true);
			break;
		default:
			break;
	}
});

// 获取下一张图片
nextBtn.onclick = function() {
	annotate.Arrays.imageAnnotateMemory.length > 0 && localStorage.setItem(taskName.textContent, JSON.stringify(annotate.Arrays.imageAnnotateMemory));  // 保存已标定的图片信息
	if (imgIndex >= imgSum) {
		imgIndex = 1;
		selectImage(1);
	}
	else {
		imgIndex++;
		selectImage(imgIndex);
	}
};

// 获取上一张图片
prevBtn.onclick = function() {
	annotate.Arrays.imageAnnotateMemory.length > 0 && localStorage.setItem(taskName.textContent, JSON.stringify(annotate.Arrays.imageAnnotateMemory));  // 保存已标定的图片信息
	if (imgIndex === 1) {
		imgIndex = imgSum;
		selectImage(imgSum);
	}
	else {
		imgIndex--;
		selectImage(imgIndex);
	}
};

document.querySelector('.selectImage').addEventListener('click', function() {
	// 弹出输入窗口，获取用户输入的数字
    var inputValue = window.prompt("请输入图片id：");
    // 将用户输入的数字保存在变量中
    if (inputValue !== null) {
        imgIndex = inputValue;
    	initImage(inputValue,imgSum);
    }
    else{
    	initImage(imgIndex,imgSum);
	}
});

function selectImage(index) {
	openBox('#loading', true);
	processIndex.innerText = imgIndex;

	// taskName.innerText是文件夹名称 example
	// let content = localStorage.getItem(taskName.textContent);
	// annotate.SetImage("http://8.130.72.138:8081/docs/imgs/0.png");
	$(document).ready(function(){
		$.get(label_url+"/getlink/",{"index":index,"taskid_ano":projectId}, function(ret){
			if (ret.task_type!=="picClass"){
				annotate.SetImage("data:image/png;base64,"+ret.image_b64,ret.label);
			}
			else{
				annotate.SetImage("data:image/png;base64,"+ret.image_b64,false);
			}
			trueimgIndex = ret.true_id;
			projectId=ret.project_id;
			progress=ret.progress;
			len_of_labeled=ret.len_of_label;
			var checked = document.getElementById("checked");
			if (ret.label){
				checked.checked = true;
				if(ret.task_type==="picClass"){
					taskName.innerText = "进度："+progress+" 标签："+ret.label+" 当前任务属于："+ret.task_type;
				}
				else{
					taskName.innerText = "进度："+progress+
					" 目前已标注了："+len_of_labeled+"张图片"+
					" 当前任务属于："+ret.task_type;
				}

			}else{
				checked.checked = false;
				taskName.innerText = "项目进度："+progress+
				" 目前已标注了："+len_of_labeled+"张图片"+
				" 当前任务属于："+ret.task_type;
			}
			// console.log(ret.label);

			// annotate.SetImage("http://8.130.72.138:8081/docs/imgs/0.png");
			// processIndex.innerText = ret.id;

		});
	});
	// let img = imgFiles[index]; // img:./static/images/example/football.jpg
	// let img = imgFiles[index].name ? window.URL.createObjectURL(imgFiles[index]) : imgFiles[index];
	// annotate.SetImage(img);
	// content ? annotate.SetImage(img, JSON.parse(content)) : annotate.SetImage(img);
}

document.querySelector('.submitData').addEventListener('click', function() {
	console.log(identity);
	if (identity==="worker"){
		let filename = taskName.textContent.split('.')[0] + '.json';
		var flag = false;
		if (annotate.Arrays.imageAnnotateMemory.length === 0){
			alert('当前图片未有有效的标定数据,确定提交？');
		}
		flag = submitData(annotate.Arrays.imageAnnotateMemory);
		if (flag===false){
			alert('保存标注失败！');
		}else{
			alert('保存标注成功！');
			annotate.Arrays.imageAnnotateMemory.length > 0 && localStorage.setItem(taskName.textContent, JSON.stringify(annotate.Arrays.imageAnnotateMemory));  // 保存已标定的图片信息
			if (imgIndex >= imgSum) {
				imgIndex = 1;
				selectImage(1);
			}
			else {
				imgIndex++;
				selectImage(imgIndex);
			}
		}
	}else{
		alert('当前身份不允许上传数据');
	}
});



function submitData(data) {
	if (!data) {
		alert('保存的数据为空');
		return false;
	}
	if (typeof data === 'object') {
		data.push({
			"true_id":trueimgIndex.toString(),
			"project_id":projectId.toString(),
		});
		data = JSON.stringify(data, undefined, 4);
		// console.log(data)
	}


	const url = label_url+'/label';  // Django 视图的 URL
	const options = {  // 定义 AJAX 请求的选项
		method: 'POST',
		body: data
	};
	fetch(url, options)  // 发送 AJAX 请求
		.then(response => {
			if (response.ok) {
				console.log('Data was saved successfully.');
				return true;
			} else {
				console.log('Error saving data.');
				return false;
			}
		})
		.catch(error => {
			console.error(error);
		});
	// let blob = new Blob([data], {type: 'text/json'}),
	// 	e = document.createEvent('MouseEvent'),
	// 	a = document.createElement('a');
	// 	a.download = filename;
	// 	a.href = window.URL.createObjectURL(blob);
	// 	a.dataset.downloadurl = ['text/json', a.download, a.href].join(':');
	// 	e.initMouseEvent('click', true, false, window,  0, 0, 0, 0, 0, false, false, false, false, 0, null);
	// 	a.dispatchEvent(e)
}

//弹出框
function openBox (e, isOpen) {
	let el = document.querySelector(e);
	let maskBox = document.querySelector('.mask_box');
	if (isOpen) {
		maskBox.style.display = "block";
		el.style.display = "block";
	}
	else {
		maskBox.style.display = "none";
		el.style.display = "none";
	}
}