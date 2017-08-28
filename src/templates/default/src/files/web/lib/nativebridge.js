var escapable = /[\\\x00-\x1f\x7f-\uffff]/g,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '\\': '\\\\'
        };

    function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

        escapable.lastIndex = 0;
        return escapable.test(string) ?
            string.replace(escapable, function (a) {
                var c = meta[a];
                return typeof c === 'string' ? c :
                    '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
            }):
            string;
    }

// this is really a singleton so despite this syntax we won't actually be creating multiple
// copies of this object's functions, etc. 
var NativeBridge = function() {

    this.initialize = function()
    {
        this.protocol = null;
        this.language = "en";
        this.appData = [];
        this.js_controller = null;
    };

	this.setProtocol = function(p)
	{
		this.protocol = p;
	};

    this.setJSController = function(controller) {
        this.js_controller = controller;
    };

    this.setLanguage = function(l)
    {
        this.language = l;
    };

    this.getAppData = function(key)
    {
        if (key === undefined) {
            return this.appData;
        }
        return this.appData[key];
    };

    this.setAppData = function(key, json_data)
    {
        this.appData[key] = JSON.parse(json_data);
    };

    this.getLanguage = function()
    {
        return this.language;
    };

    this.getJSValue = function(property)
    {
        this.sendMessage("get_value_from_js", eval(property));
    };

	this.sendMessage = function()
	{
		var url = arguments[0];
		if (arguments.length > 1)
		{
			url += "?";
			for (var i = 1; i < arguments.length; i++) {
                var value = arguments[i];
                if (value.constructor === [].constructor || value.constructor === {}.constructor) {
                    value = JSON.stringify(value);
                }
                url += encodeURIComponent(value) + "&";
            }
            // cut off the last & character
            url = url.substring(0, url.length - 1);
		}

        if (this.protocol !== null) {
            console.log("sending message " + url);
            $.ajax(this.protocol + url);
        } else if (this.js_controller !== null) {
            var methodString = "this.js_controller." + arguments[0].replace("/", ".") + "(";
            if (arguments.length > 1)
            {
                for (var n = 1; n < arguments.length; n++) {
                    methodString += '"' + arguments[n] + '",';
                }
                methodString = methodString.substring(0, methodString.length - 1);
            }
            methodString += ");";
            console.log("sending message " + methodString);
            try {
                eval(methodString);
            } catch(err) {
                console.log(err);
            }
        } else {
            console.log("Not handling message " + url);
        }
	};

};

var bridge = new NativeBridge();
// weird to have to call methods to initialize but it seems this is the most straightforward way
bridge.initialize();