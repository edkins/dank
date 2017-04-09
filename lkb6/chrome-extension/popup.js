function updateTable(obj)
{
	var types=['like','love','haha','wow','sad','angry'];
	for (var i = 0; i < types.length; i++)
	{
		var type=types[i];
		var text = '';
		if (obj != undefined && obj.summary != undefined)
		{
			text = obj.summary[type];
		}
		document.getElementById(type).textContent = text;
	}
}
document.addEventListener('DOMContentLoaded', function () {
	chrome.runtime.getBackgroundPage(function(bgPage) {
		bgPage.register(updateTable);
	});
});
