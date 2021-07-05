import { Component } from '@angular/core';
import {FormBuilder, Validators} from '@angular/forms';
import { formatDate } from '@angular/common';
import { BackendService } from './backendService';

@Component({
    selector: 'requestcover',
    templateUrl: './request-cover.component.html',
    styleUrls: ['./request-cover.component.css']
})
export class RequestCoverComponent {
    
    requestForm;
    selectedStore;
    shopList: Array<Object> = []
    numberOfRecipients: Array<Object> = []
    confrimationScreen = false

    constructor(private formBuilder: FormBuilder,
        private backendService: BackendService) {}

    ngOnInit(){
        this.backendService.getAllShopNames().subscribe((data) => 
        { for(var entry = 0; entry < data.length; entry++){ 
            this.shopList.push(data[entry]); 
        }})

        this.requestForm = this.formBuilder.group({
            store: ['', Validators.required],            
            role: ['', Validators.required],
            date: [formatDate(Date.now(), 'yyyy-MM-dd', 'en'), Validators.required],
            startTime: ['00:00', Validators.required],
            endTime: ['00:00', Validators.required],
            distanceFilter: ['N/A', Validators.required],
            timeFilter: ['N/A', Validators.required]
        });
    }
    
    onSubmit(){
      this.backendService.sendCoverRequest(this.requestForm.value);
      this.shopList = []
      this.requestForm.reset(); 
      this.confrimationScreen = false
      this.ngOnInit();     
    }

    onContinue(){
        this.numberOfRecipients = []
        this.backendService.getNumberOfRecipients(this.requestForm.value).subscribe((data) => 
        { for(var entry = 0; entry < data.length; entry++){ 
            this.numberOfRecipients.push(data[entry]); 
        }})
        this.confrimationScreen = true
    }

    onBack(){
        this.confrimationScreen = false
    }

    isInvalid(control) {
        return this.requestForm.controls[control].invalid &&
                this.requestForm.controls[control].touched;
            }
    
    isIncomplete() {
        return this.isInvalid('store') ||
                this.isInvalid('role') ||
                this.isInvalid('date') ||
                this.isInvalid('startTime') ||
                this.isInvalid('endTime') ||
                this.isInvalid('distanceFilter') ||
                this.isInvalid('timeFilter') ||
                this.isUnTouched();
    }

    isUnTouched() {
        return this.requestForm.controls.role.pristine;
    }

}