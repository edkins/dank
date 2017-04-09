var retries = 0;
var patience = 1;

var retrievedData = undefined;
var listener = undefined;

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
	patience = Math.min(patience * 2, 12);
	var obj = undefined;
	if (this.status == 200)
	{
		var obj = JSON.parse(this.responseText);
		if ('summary' in obj)
		{
			var innerHTML = ''
			var types = ['like','love','haha','wow','sad','angry']
			var total = 0;
			for (var i = 0; i < 6; i++)
			{
				var type = types[i];
				total += obj.summary[type];
			}
			text = '' + total;
			chrome.browserAction.setBadgeText({ text: text });
			retries = 1;
			patience = 1;
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

	retrievedData = obj;
	if (listener != undefined)
	{
		listener(obj);
	}
}

function register(func)
{
	listener = func;
	func(retrievedData);
}

poll();
window.setInterval(poll, 5000);
