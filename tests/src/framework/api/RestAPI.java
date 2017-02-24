package framework.api;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.List;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

import framework.pages.TopPage;

public class RestAPI {
	private WebDriver driver;
	
	public RestAPI(WebDriver driver){
		this.driver = driver;
	}
	
	public String addMachine(String ipaddr, String username){
		String url = "curl -X 'POST' http://localhost:5000/add/" + ipaddr + ":" + username;
		StringBuffer output = new StringBuffer();
		
	    String[] cmd = { "/bin/sh", "-c", url };
	    String line;
	    try{
		    Process proc = Runtime.getRuntime().exec(cmd);
		    BufferedReader is = new BufferedReader(new InputStreamReader(proc.getInputStream()));
		    while ((line = is.readLine()) != null) {
		    	output.append(line.trim());
		    }

	    }
	    catch(IOException e){
	    	System.out.println(e);
	    }
	    
	    //System.out.printf("Added a machine(%s) via RESUful API: " + output.toString() + "\n", ipaddr);
	    return output.toString();
   
	}
	
	public String addMachine(String ipaddr, String username, String password){
		String url = "curl -X 'POST' http://localhost:5000/add/" + ipaddr + ":" + username + ":" + password;
		StringBuffer output = new StringBuffer();
		
	    String[] cmd = { "/bin/sh", "-c", url };
	    String line;
	    try{
		    Process proc = Runtime.getRuntime().exec(cmd);
		    BufferedReader is = new BufferedReader(new InputStreamReader(proc.getInputStream()));
		    while ((line = is.readLine()) != null) {
		    	output.append(line.trim());
		    }

	    }
	    catch(IOException e){
	    	System.out.println(e);
	    }
	    
	    //System.out.printf("Added a machine(%s) via RESUful API: " + output.toString() + "\n", ipaddr);
	    return output.toString();
   
	}
	
	public String deleteMachine(String ipaddr){
		String url = "curl -X 'DELETE' http://localhost:5000/delete/" + ipaddr;
		StringBuffer output = new StringBuffer();
		
	    String[] cmd = { "/bin/sh", "-c", url };
	    String line;
	    try{
		    Process proc = Runtime.getRuntime().exec(cmd);
		    BufferedReader is = new BufferedReader(new InputStreamReader(proc.getInputStream()));
		    while ((line = is.readLine()) != null) {
		    	output.append(line.trim());
		    }

	    }
	    catch(IOException e){
	    	System.out.println(e);
	    }
	    
	    //System.out.printf("Deleted machines(%s) via RESUful API: " + output.toString() + "\n", ipaddr);
	    return output.toString();
   
	}
	
	public void deleteAllUnknownMachines(){
		// Delete all machines whose hostname is #Unknown
		TopPage topPage = new TopPage(driver);
        String deleteIPs = "";
        List<WebElement> hostNameList = topPage.getHostNameList();
        List<WebElement> ipAddrList = topPage.getIpAddressList();
        
        boolean hasUnknown = false;
        for (int i=0; i<hostNameList.size(); i++){
        	if (hostNameList.get(i).getText().contains("#Unknown")){
        		hasUnknown = true;
        		deleteIPs += ipAddrList.get(i).getText() + ",";
        	}
        }
        
        if (hasUnknown){
        	deleteMachine(deleteIPs.substring(0, deleteIPs.length()-1));
        }   
	}
}