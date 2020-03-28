package org.kosoftworks.pyeverywhere;

import android.webkit.WebView;
import android.webkit.WebViewClient;

public class PEWebViewClient extends WebViewClient 
{
	private WebViewCallbacks callback;

	public void setWebViewCallbacks(WebViewCallbacks c)
	{
		callback = c;
	}

	@Override
	public void onPageFinished(WebView view, String url) {
        callback.pageLoadComplete(view, url);
    }

	@Override
	public boolean shouldOverrideUrlLoading(WebView view, String url) {
		return callback.shouldLoadURL(view, url);
		
	}

}