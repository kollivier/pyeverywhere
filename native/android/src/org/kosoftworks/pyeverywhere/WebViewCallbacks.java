package org.kosoftworks.pyeverywhere;

import android.webkit.WebView;

public interface WebViewCallbacks 
{
	public void pageLoadComplete(WebView view, String url);
	
	public boolean shouldLoadURL(WebView view, String url);
}