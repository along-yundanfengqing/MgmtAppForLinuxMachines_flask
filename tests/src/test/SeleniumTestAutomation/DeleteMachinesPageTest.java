package test.SeleniumTestAutomation;

import java.util.List;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import framework.pages.DeletePage;
import test.SeleniumTestAutomation.base.BaseTest;

public class DeleteMachinesPageTest extends BaseTest {
	private DeletePage deletePage;
    private final String TEST_IP1 = "1.1.1.1";
    private final String TEST_IP2 = "2.2.2.2";
    private final String TEST_USERNAME = "test_user";
    private final String TEST_PASSWORD = "test_password";
    private List<WebElement> machineList;
    private List<WebElement> hostNameList;
    private List<WebElement> ipAddressList;
    private List<WebElement> osDistributionImgNameList;
    
    @BeforeMethod
    public void beforeMethod() {
    	restAPI.deleteAllUnknownMachines();
    }
    
    @Test(description="Verify delete machines page - success")
    public void verifyDeleteMachines() {
    	restAPI.addMachine(TEST_IP1, TEST_USERNAME, TEST_PASSWORD);
    	restAPI.addMachine(TEST_IP2, TEST_USERNAME, TEST_PASSWORD);
    	deletePage = topPage.clickDeleteMachinesButton();
    	
    	List<WebElement> checkBoxes = deletePage.getCurrentMachineCheckBoxes();
    	for (WebElement checkBox: checkBoxes){
    		System.out.println(checkBox.getText());
    		if (checkBox.getAttribute("value").contains(TEST_IP1) || checkBox.getAttribute("value").contains(TEST_IP2)){
    			checkBox.click();
    		}
    	}
    	
    	deletePage.getDeleteButton().submit();
    	String topPageFlashMessage = topPage.getFlashMessageField().getText();
    	Assert.assertTrue(topPageFlashMessage.contains("Deleted") && topPageFlashMessage.contains(TEST_IP1) && topPageFlashMessage.contains(TEST_IP2), topPageFlashMessage);    	
    }
    	
    @Test(description="Verify delete machines page - success")
    public void verifyDeleteMachinesNoSelection() {
    	deletePage = topPage.clickDeleteMachinesButton();
    	deletePage.getDeleteButton().submit();
    	String flashMessage = deletePage.getFlashMessageField().getText();
    	Assert.assertTrue(flashMessage.contains("Select machines to delete"), flashMessage);
    	
    }
}