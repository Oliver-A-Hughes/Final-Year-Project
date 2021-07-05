import { Component } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { BackendService } from './backendService';

@Component({
    selector: 'shop',
    templateUrl: './shop.component.html',
    styleUrls: ['./shop.component.css']
})
export class ShopComponent {

    editShopDetails = false
    deleteShop = false
    editShopForm;

    // Variables for editing shop details 
    shopName = ''
    address = ''
    city = ''
    region = ''

    constructor(private backendService: BackendService,
        private formBuilder: FormBuilder,
        private route: ActivatedRoute,
        private router: Router) {}

    ngOnInit(){
        if (this.editShopDetails == true)
        {
            this.getEditForm();
        }
        else
        {
            this.backendService.getSingleShop(this.route.snapshot.params.id);
        }
    }

    getEditForm(){
        this.editShopForm = this.formBuilder.group({
            shopName: [this.shopName, Validators.required],            
            address: [this.address, Validators.required],
            city: [this.city, Validators.required],
            region: [this.region, Validators.required]
        });
    }

    editButtonClicked(shopName, address, city, region){
        this.editShopDetails = true
        this.shopName = shopName
        this.address = address
        this.city = city
        this.region = region
        this.ngOnInit();
    }

    onSubmit(){
        this.backendService.editShop(this.route.snapshot.params.id , this.editShopForm.value).subscribe();
        this.editShopDetails = false
        this.ngOnInit();
    }
    
    cancelButtonClicked(){
        if (this.editShopDetails == true){
            this.editShopDetails = false
        }
        else if (this.deleteShop == true){
            this.deleteShop = false
        }
        this.ngOnInit()
    }

    isInvalid(control) {
        return this.editShopForm.controls[control].invalid &&
                this.editShopForm.controls[control].touched;
            }
    
    isIncomplete() {
        return this.isInvalid('shopName') ||
                this.isInvalid('address') ||
                this.isInvalid('city') ||
                this.isInvalid('region')
    }

    deleteButtonClicked(){
        this.deleteShop = true
        this.ngOnInit()
    }

    confirmDeletion(){
        this.backendService.deleteShop(this.route.snapshot.params.id)
        this.router.routeReuseStrategy.shouldReuseRoute = () => false;
        this.router.onSameUrlNavigation = 'reload';
        this.router.navigate(['/shops']);
    }

}