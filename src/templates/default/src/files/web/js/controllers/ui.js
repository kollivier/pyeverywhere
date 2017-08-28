console.log('Initializing UI');

// UI Controller singleton
var ui = {
    // Application Constructor
    templates: ["base", "home"],
    compiledTemplates: {},
    spinner: null,
    currentDialog: null,

    initialize: function() {
        this.compileTemplates();
        $('body').html(this.compiledTemplates["base"]());
    },

    compileTemplates: function() {
        for (i=0; i < this.templates.length; i++)
        {
            this.compileTemplate(this.templates[i]);
        }
    },

    compileTemplate: function(templateName)
    {
        this.compiledTemplates[templateName] = Handlebars.compile($("#" + templateName + "-tpl").html());
        if (this.compiledTemplates[templateName] === undefined) {
            console.log("Unable to compile template " + templateName + "?");
        }
    },

    applyTemplate: function(templateName, data) {
        if (typeof data == 'string' || data instanceof String) {
            data = JSON.parse(data);
        }
        console.log("Applying template for " + templateName + " with data:");
        console.log(" " + JSON.stringify(data));
        return this.compiledTemplates[templateName](data);
    },

    setView: function(templateName, data) {
        this.hideProgressBar();
        var htmlText = this.applyTemplate(templateName, data);
        $('#view').html(htmlText);
    },

    setStatus: function(text) {
        $('#status').text(text);
    },
    
    showProgressBar: function() {
        this.spinner = new Spinner().spin();
        $('body').after(this.spinner.el);
    },

    hideProgressBar: function() {
        if (this.spinner !== null) {
            this.spinner.stop();
        }
    },
    
    showDialog: function(dialogName, timeoutFunction, text)
    {
        this.hideProgressBar();
        this.closeDialog();
        this.currentDialog = dialogName;
        $(dialogName).dialog({
          autoOpen: false,
          width: 'auto',
          show: 'fade',
          hide: 'fade',
        });

        if (text !== undefined) {
            $(dialogName).text(text);
        }
        $(dialogName).siblings('div.ui-dialog-titlebar').remove();
        $(dialogName).dialog('open');

        setTimeout(timeoutFunction, 3000);
    },

    closeDialog: function(selector) {
        if (selector === undefined) {
            selector = this.currentDialog;
        }
        if (selector !== null) {
            $(selector).dialog('close');
        }
        this.currentDialog = null;
    },
};

function error_handler(error, url, line,col,errorobj) {
   bridge.sendMessage("web_error", "JavaScript exception", "line: " + line + "col: " + col + "\n\n" + error);
}

window.onerror = error_handler;
