// after the app loads, call mock_app.load() to start testing the UI.

var mock_app = {
    data: {
    },

    make_it_so: function() {
        this_just_in("You can have a mock JS controller to pump dummy data and test the UI from the browser.")
    },

    load_complete: function() {
        app.ui.setView("home");
    }
};

bridge.setJSController(mock_app);
            