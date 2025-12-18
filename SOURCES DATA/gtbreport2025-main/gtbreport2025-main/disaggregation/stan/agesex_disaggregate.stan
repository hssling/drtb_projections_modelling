// Sampling of age/sex disaggregation over time
data{
  int nas;   // number of age/sex 
  int ntime; // number of times
  int niso;  // number of countries
  matrix[ntime,niso] IncD_mean; // mid-point inc estimates
  matrix[niso,nas] Notes[ntime];// notifications
  real ustol; // undershoot penalty scale
  real tstol; // time smoothing scale
  int pattern[ntime,niso]; // pattern of missingness
  matrix[niso,nas-1] YM;   // prios for Y mean
  matrix[niso,nas-1] YS;   // prios for Y SD  
}

transformed data{
  row_vector[16] w2 = [1,2,2,1,1,1,1,1,1,2,2,1,1,1,1,1]; // pattern 2
  row_vector[14] w4 = [3,2,1,1,1,1,1,3,2,1,1,1,1,1]; // pattern 4
  row_vector[6] w5 = [1,2,5,1,2,5]; // pattern 5
  row_vector[4] w6 = [3,5,3,5]; // pattern 6 
  matrix[niso,16] Notes2[ntime]; // pattern 2
  matrix[niso,14] Notes4[ntime]; // pattern 4
  matrix[niso,6] Notes5[ntime]; // pattern 5
  matrix[niso,4] Notes6[ntime]; // pattern 6
  vector[niso*(nas-1)] YMV = to_vector(YM);
  vector[niso*(nas-1)] YSV = to_vector(YS);  
  real eps = 1.0; // tolerance parameter
  for(t in 1:ntime){
    for(iso in 1:niso){
      // --- other Notes: NOTE requires judicious uses of zeros in input... 
      // -- 2
      // old school
      // 0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65+      
      // M:
      Notes2[t,iso,1] = Notes[t,iso,1];
      Notes2[t,iso,2] = Notes[t,iso,2] + Notes[t,iso,3];//5-14
      Notes2[t,iso,3] = Notes[t,iso,4] + Notes[t,iso,5];//15-24
      Notes2[t,iso,4:8] = Notes[t,iso,6:10];
      // F:
      Notes2[t,iso,9] = Notes[t,iso,11];
      Notes2[t,iso,10] = Notes[t,iso,12] + Notes[t,iso,13];//5-14
      Notes2[t,iso,11] = Notes[t,iso,14] + Notes[t,iso,15];//15-24
      Notes2[t,iso,12:16] = Notes[t,iso,16:20];
      // -- 4
      // M:
      Notes4[t,iso,1] = Notes[t,iso,1] + Notes[t,iso,2] + Notes[t,iso,3];//0-14
      Notes4[t,iso,2] = Notes[t,iso,4] + Notes[t,iso,5];//15-24
      Notes4[t,iso,3:7] = Notes[t,iso,6:10];
      // F:
      Notes4[t,iso,8] = Notes[t,iso,11] + Notes[t,iso,12] + Notes[t,iso,13];//0-14
      Notes4[t,iso,9] = Notes[t,iso,14] + Notes[t,iso,15];//15-24
      Notes4[t,iso,10:14] = Notes[t,iso,16:20];
      // -- 5
      // (0-14,0-4,5-14 only)
      // 0-4, 5-14, 15+      
      // M:
      Notes5[t,iso,1] = Notes[t,iso,1];
      Notes5[t,iso,2] = Notes[t,iso,2] + Notes[t,iso,3];//5-14
      Notes5[t,iso,3] = sum(Notes[t,iso,4:10]);//15+
      // F:
      Notes5[t,iso,4] = Notes[t,iso,11];
      Notes5[t,iso,5] = Notes[t,iso,12] + Notes[t,iso,13];//5-14
      Notes5[t,iso,6] = sum(Notes[t,iso,14:20]);//15+
      // -- 6
      // (0-14 only):
      // 0-14, 15+      
      // M:
      Notes6[t,iso,1] = Notes[t,iso,1] + Notes[t,iso,2] + Notes[t,iso,3];//5-14
      Notes6[t,iso,2] = sum(Notes[t,iso,4:10]);//15+
      // F:
      Notes6[t,iso,3] = Notes[t,iso,11] + Notes[t,iso,12] + Notes[t,iso,13];//5-14
      Notes6[t,iso,4] = sum(Notes[t,iso,14:20]);//15+
    }
  }    
}

parameters{
  // nas = number of age/sex cats
  // ntime = number of times
  // niso = number of countries
  matrix[niso,nas-1] Y[ntime]; // latent variable
}

transformed parameters{
  matrix[niso,nas] P[ntime];// splits as probabilities (pattern 3)
  matrix[niso,nas] ICAS[ntime]; // incidence by country age & sex
  for(t in 1:ntime){
    for(iso in 1:niso){
      // --- pattern 3: complete
      P[t,iso,:] = softmax(append_col([0.0],Y[t,iso,:])')';
      ICAS[t,iso,:] = IncD_mean[t,iso] * P[t,iso,:]; // split
    }
  }
}

model{
  // done here so as not to clog up memory
  matrix[niso,16] P2[ntime]; // pattern 2
  matrix[niso,14] P4[ntime]; // pattern 4
  matrix[niso,6] P5[ntime]; // pattern 5
  matrix[niso,4] P6[ntime]; // pattern 6 
  matrix[niso,16] ICAS2[ntime]; // pattern 2
  matrix[niso,14] ICAS4[ntime]; // pattern 4
  matrix[niso,6] ICAS5[ntime]; // pattern 5
  matrix[niso,4] ICAS6[ntime]; // pattern 6
  for(t in 1:ntime){
    for(iso in 1:niso){
      // --- other Ps: 
      // -- 2
      // M:
      P2[t,iso,1] = P[t,iso,1];
      P2[t,iso,2] = P[t,iso,2] + P[t,iso,3];//5-14
      P2[t,iso,3] = P[t,iso,4] + P[t,iso,5];//15-24
      P2[t,iso,4:8] = P[t,iso,6:10];
      // F:
      P2[t,iso,9] = P[t,iso,11];
      P2[t,iso,10] = P[t,iso,12] + P[t,iso,13];//5-14
      P2[t,iso,11] = P[t,iso,14] + P[t,iso,15];//15-24
      P2[t,iso,12:16] = P[t,iso,16:20];
      // -- 4
      //old old school (no split of 0-14)
      // 0-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65+
      // M:
      P4[t,iso,1] = P[t,iso,1] + P[t,iso,2] + P[t,iso,3];//0-14
      P4[t,iso,2] = P[t,iso,4] + P[t,iso,5];//15-24
      P4[t,iso,3:7] = P[t,iso,6:10];
      // F:
      P4[t,iso,8] = P[t,iso,11] + P[t,iso,12] + P[t,iso,13];//0-14
      P4[t,iso,9] = P[t,iso,14] + P[t,iso,15];//15-24
      P4[t,iso,10:14] = P[t,iso,16:20];
      // -- 5
      // M:
      P5[t,iso,1] = P[t,iso,1];
      P5[t,iso,2] = P[t,iso,2] + P[t,iso,3];//5-14
      P5[t,iso,3] = sum(P[t,iso,4:10]);//15+
      // F:
      P5[t,iso,4] = P[t,iso,11];
      P5[t,iso,5] = P[t,iso,12] + P[t,iso,13];//5-14
      P5[t,iso,6] = sum(P[t,iso,14:20]);//15+
      // -- 6
      // M:
      P6[t,iso,1] = P[t,iso,1] + P[t,iso,2] + P[t,iso,3];//5-14
      P6[t,iso,2] = sum(P[t,iso,4:10]);//15+
      // F:
      P6[t,iso,3] = P[t,iso,11] + P[t,iso,12] + P[t,iso,13];//5-14
      P6[t,iso,4] = sum(P[t,iso,14:20]);//15+
      // --- other Ns
      ICAS2[t,iso,:] = IncD_mean[t,iso] * P2[t,iso,:]; // split
      ICAS4[t,iso,:] = IncD_mean[t,iso] * P4[t,iso,:]; // split
      ICAS5[t,iso,:] = IncD_mean[t,iso] * P5[t,iso,:]; // split
      ICAS6[t,iso,:] = IncD_mean[t,iso] * P6[t,iso,:]; // split
    }
  }       

    

  // prior for split
  for(t in 1:ntime){
    to_vector(Y[t]) ~ normal(YMV,YSV);
  }

  // data undershoot penalty NOTE weighting! 
  for(t in 1:ntime){
    for(cn in 1:niso){
      if(pattern[t,cn]==1){ //no data for split
        // no penalty
        } else if(pattern[t,cn]==2){ //old school
          // 0-4, 5-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65+
          target += -sum(exp( w2 .* (Notes2[t][cn,:] ./ (ICAS2[t][cn,:]+eps) - 1.0) / ustol ));
        } else if(pattern[t,cn]==3){ // complete data pattern
          // 0-4, 5-9, 10-14, 15-19, 20-24 25-34, 35-44, 45-54, 55-64, 65+
          target += -sum(exp( (Notes[t][cn,:] ./ (ICAS[t][cn,:]+eps) - 1.0) / ustol ));
        } else if(pattern[t,cn]==4){ //old old school (no split of 0-14)
          // 0-14, 15-24, 25-34, 35-44, 45-54, 55-64, 65+
          target += -sum(exp( w4 .* (Notes4[t][cn,:] ./ (ICAS4[t][cn,:]+eps) - 1.0) / ustol ));
        } else if(pattern[t,cn]==5){// (0-14,0-4,5-14 only)
          // 0-4, 5-14, 15+
          target += -sum(exp( w5 .* (Notes5[t][cn,:] ./ (ICAS5[t][cn,:]+eps) - 1.0) / ustol ));
        } else if(pattern[t,cn]==6){// (0-14 only):
          // 0-14, 15+
          target += -sum(exp( w6 .* (Notes6[t][cn,:] ./ (ICAS6[t][cn,:]+eps) - 1.0) / ustol ));
        }
    }
  }

  // smoothing
  for(t in 2:ntime){
    target += -sum((Y[t]-Y[t-1]).^2) / tstol;
  }

}
