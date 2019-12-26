// easiest kalman's filter realization
class Kalman {
  private:
    float deviation = 0.25;
    float coeff = 0.05;
    float pc = 0.0;
    float g = 0.0;
    float p = 1.0;
    float xp = 0.0;
    float zp = 0.0;
    float xe = 0.0;
  public:
    Kalman() { }
    Kalman(float dev, float c) {
      this->deviation = dev;
      this->coeff = c;
    }
    float filter(float val) {
      this->pc = this->p + this->coeff;
      this->g = this->pc / (this->pc + this->deviation);
      this->p = (1.0 - this->g) * this->pc;
      this->xp = this->xe;
      this->zp = this->xp;
      this->xe = this->g * (val - this->zp) + this->xp;
      return this->xe;
    }
};
