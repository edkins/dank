var retries = 0;
var patience = 1;

function poll()
{
	retries--;
	if (retries <= 0)
	{
		retries = 0;
		xhr = new XMLHttpRequest();
		xhr.addEventListener('load', handleResult);
		xhr.addEventListener('error', handleError);
		xhr.addEventListener('abort', handleAbort);
		xhr.open('GET', 'https://opendank.org/api/shenanigans/lkb-666/summary');
		xhr.send();
	}
}

function handleError()
{
	chrome.browserAction.setBadgeText({ text: '?' });
}
function handleAbort()
{
	chrome.browserAction.setBadgeText({ text: '?' });
}

function handleResult()
{
	retries = patience;
	patience = Math.min(patience * 2, 60);
	if (this.status == 200)
	{
		var obj = JSON.parse(this.responseText);
		if ('summary' in obj)
		{
			var innerHTML = ''
			var types = ['like','love','haha','wow','sad','angry']
			var maximum = 0;
			for (var i = 0; i < 6; i++)
			{
				var type = types[i];
				maximum = Math.max(maximum, obj.summary[type]);
			}
			text = '' + maximum;
			chrome.browserAction.setBadgeText({ text: text });
		}
		else
		{
			chrome.browserAction.setBadgeText({ text: '?' });
		}
	}
	else
	{
		chrome.browserAction.setBadgeText({ text: '?' });
	}
}

window.setInterval(poll, 5000);
