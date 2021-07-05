import { Component } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { BackendService } from './backendService';

@Component({
    selector: 'shopList',
    templateUrl: './shop-list.component.html',
    styleUrls: ['./shop-list.component.css']
})
export class ShopListComponent {

    addShop = false
    shopForm

    constructor(private backendService: BackendService,
        private formBuilder: FormBuilder,) {}
    
    async ngOnInit(){
        if(this.addShop == true)
        {
            this.getAddForm();
        }
        else
        {
            this.backendService.shopsListRefreshNeeded
            .subscribe(() => {
               this.backendService.getAllShops();
            });
            this.backendService.getAllShops();
        }      
    }

    getAddForm(){
        this.shopForm = this.formBuilder.group({
            shopName: ['', Validators.required],            
            address: ['', Validators.required],
            city: ['', Validators.required],
            region: ['UK', Validators.required]
        });
    }

    addButtonClicked(){
        this.addShop = true
        this.ngOnInit();
    }

    cancelButtonClicked(){
        this.addShop = false
        this.ngOnInit()  
    }

    onSubmit(){
        this.backendService.addShop(this.shopForm.value).subscribe();
        this.addShop = false
        this.ngOnInit();
    }

    isInvalid(control) {
        return this.shopForm.controls[control].invalid &&
                this.shopForm.controls[control].touched;
            }
    
    isIncomplete() {
        return this.isInvalid('shopName') ||
                this.isInvalid('address') ||
                this.isInvalid('city') ||
                this.isInvalid('region') ||
                this.isUnTouched();
    }

    isUnTouched() {
        return this.shopForm.controls.shopName.pristine ||
                this.shopForm.controls.address.pristine ||
                this.shopForm.controls.city.pristine;
    }
    
}